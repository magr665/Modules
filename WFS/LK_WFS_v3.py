"""
WFSClient klassen bruges til at kommunikere med WFS-tjenester.

Klassen håndterer automatisk:
- GetCapabilities forespørgsel for at hente metadata
- Opdeling af store datamængder i mindre bidder via bbox'e
- Konvertering af datofelter
- Klipning af data til bbox
- Authentication via brugernavn/kodeord

Parametre ved initialisering:
    url (str): URL til WFS-tjenesten
    username (str, optional): Brugernavn til authentication
    password (str, optional): Kodeord til authentication
    bbox (list, optional): Bounding box [minx, miny, maxx, maxy]
    debug (bool, optional): Debug mode, default False
    maxfeatures (int, optional): Max antal features per forespørgsel
    outputformat (str, optional): Output format --> Prøv at bruge 'json' hvis den ellers ikke virker
    params (dict, optional): Ekstra parametre til WFS forespørgsler

Eksempel:
    >>> wfs = WFS('https://example.com/wfs', 
                  username='user',
                  password='pass',
                  bbox=[570000, 6200000, 580000, 6210000])
    >>> gdf = wfs.get_feature('kommuner')

    params kan f.eks. være:
    >>> params = {'whoami': 'Lemvig Kommune'}


Bemærk:
    Kræver geopandas, pandas, requests, lxml, shapely og fiona installeret
"""
import pandas as pd
import geopandas as gpd
import fiona
fiona.drvsupport.supported_drivers['WFS'] = 'r'
import requests
from requests.auth import HTTPBasicAuth
from xml.etree import ElementTree as ET
import lxml.etree as etree
from shapely.geometry import box
from io import StringIO

import ssl
ssl._create_default_https_context = ssl._create_unverified_context

class WFSClient:
    """
    WFSClient klassen bruges til at kommunikere med WFS-tjenester.

    **SKAL VÆRE WFS VERSION 2.0.0 ELLER HØJERE FOR AT FUNKTIONEN MED PAGING VIRKER!!**

    Klassen håndterer automatisk:
    - GetCapabilities forespørgsel for at hente metadata 
    - Opdeling af store datamængder i mindre bidder via bbox'e
    - Konvertering af datofelter
    - Klipning af data til bbox
    - Authentication via brugernavn/kodeord

    Parametre ved initialisering:
        url (str): URL til WFS-tjenesten
        username (str, optional): Brugernavn til authentication
        password (str, optional): Kodeord til authentication  
        bbox (list, optional): Bounding box [minx, miny, maxx, maxy]
        debug (bool, optional): Debug mode, default False
        maxfeatures (int, optional): Max antal features per forespørgsel
        params (dict, optional): Ekstra parametre til WFS forespørgsler
    """
    def __init__(self, url: str, **kwargs):
        self.url = url
        for key, value in kwargs.items():
            setattr(self, key, value)

        self.spec_resp = None

        if hasattr(self, 'logger'):
            self.__logger = self.logger
        else:
            self.__logger = None

        ## check for outputformat
        if hasattr(self, 'outputformat'):
            self.__outputFormat = self.outputformat
        else:
            self.__outputFormat = None

        if hasattr(self, 'paging'):
            self.__paging = self.paging
        else:
            self.__paging = True

        ## check if debug is set
        if hasattr(self, 'debug'):
            self.__debug = self.debug
            pd.set_option('display.max_rows', None)  # Vis alle rækker
            pd.set_option('display.max_columns', None)  # Vis alle kolonner
        else:
            self.__debug = False
            
        self.__params = {
            'service': 'WFS',
            'request': 'GetCapabilities'}
        
        if hasattr(self, 'params'):
            self.__params.update(self.params)
        if self.__debug: print('params:', self.__params)     

        ## check if username and password are provided together and add to params
        if (hasattr(self, 'username') and not hasattr(self, 'password')) or (hasattr(self, 'password') and not hasattr(self, 'username')):
            raise ValueError('Both username and password must be provided')

        if hasattr(self, 'username') and hasattr(self, 'password'):
            self.__params['username'] = self.username
            self.__params['password'] = self.password
        else:
            self.username = None
            self.password = None

        ## get capabilities
        url = requests.Request('GET', self.url, params=self.__params).prepare().url
        if self.__debug: print('GetCapabilities url:', url)
        if self.__logger:
            self.__logger.info(f'WFS GetCapabilities URL: {url}') 
        response = requests.get(url)
        root = etree.XML(response.content)
        if self.__debug: 
            print('GetCapabilities response:', root)
        self.get_capabilities_root = root
        self.__namespace = self.get_capabilities_root.nsmap
        self.version = root.attrib['version']
        if self.version in ('1.0.0', '1.1.0'):
            raise ValueError('WFS version 1.0.0 and 1.1.0 are not supported, please use WFS version 2.0.0 or higher')
        self.feature_list = self.__get_feature_list()
        self.operations = self.__get_operations()
        
        if 'GetFeature' in self.operations and 'parameters' in self.operations['GetFeature']:
            if 'resultType' in self.operations['GetFeature']['parameters'] and 'hits' in self.operations['GetFeature']['parameters']['resultType']:
                self.__can_get_hits = True
            else:
                self.__can_get_hits = False
        else:
            self.__can_get_hits = False

        if hasattr(self, 'maxfeatures'):
            self.maxfeatures = self.maxfeatures
            if self.__debug: print('Using provided maxfeatures:', self.maxfeatures)
        else:
            self.maxfeatures = self.__get_max_features()
            if self.__debug: print('Using default maxfeatures from GetCapabilities:', self.maxfeatures)

        if self.__logger:
            self.__logger.info(f'WFS Max Features: {self.maxfeatures}')

        if hasattr(self, 'bbox'):
            if not isinstance(self.bbox, list):
                raise ValueError('bbox must be a list of coordinates [minx, miny, maxx, maxy]')
            if len(self.bbox) != 4:
                raise ValueError('bbox must be a list of coordinates [minx, miny, maxx, maxy]')
            self.bboxes = [[str(b) for b in self.bbox]]
            self.__default_bbox = self.bboxes[0]
            self.__missing_default_bbox = False
        else:
            self.bboxes = None
            self.__default_bbox = None
            self.__missing_default_bbox = True

    def __get_max_features(self):
        """
        Get the maximum number of features that can be returned by the WFS service.
        """
        constraint = self.get_capabilities_root.find('.//{*}Constraint[@name="CountDefault"]', namespaces=self.get_capabilities_root.nsmap)
        if constraint is not None:
            maxfeatures = constraint.find('.//{*}DefaultValue', namespaces=self.get_capabilities_root.nsmap)
            if maxfeatures is not None:
                return int(maxfeatures.text)
        print('No max features found, defaulting to 10000')
        return 10000

    def __get_feature_list(self):
        """
        Henter liste over feature lag fra WFS-tjenesten.

        Funktionen laver en liste over tilgængelige feature lag via GetCapabilities.
        Der hentes navn, titel, beskrivelse, koordinatsystem og bbox for hvert lag.

        Returnerer:
            dict: Dictionary med feature lag og deres metadata
        """
        feature_list = {}
        for feature_type in self.get_capabilities_root.findall(f'.//{{*}}FeatureType', namespaces=self.__namespace):
            feature = {}
            feature['name'] = feature_type.find(f'{{*}}Name', namespaces=self.__namespace)
            if feature['name'] is not None:
                feature['name'] = feature['name'].text
            feature['title'] = feature_type.find(f'{{*}}Title', namespaces=self.__namespace)
            if feature['title'] is not None:
                feature['title'] = feature['title'].text
            feature['abstract'] = feature_type.find(f'{{*}}Abstract', namespaces=self.__namespace)
            if feature['abstract'] is not None:
                feature['abstract'] = feature['abstract'].text
            feature['srs'] = feature_type.find(f'{{*}}DefaultCRS', namespaces=self.__namespace)
            if feature['srs'] is not None:
                feature['srs'] = feature['srs'].text
            feature['bbox'] = feature_type.find(f'{{*}}WGS84BoundingBox', namespaces=self.__namespace)
            if feature['bbox'] is not None:
                feature['bbox'] = [float(feature['bbox'].find(f'{{*}}LowerCorner', namespaces=self.__namespace).text.split()[0]),
                                   float(feature['bbox'].find(f'{{*}}LowerCorner', namespaces=self.__namespace).text.split()[1]),
                                   float(feature['bbox'].find(f'{{*}}UpperCorner', namespaces=self.__namespace).text.split()[0]),
                                   float(feature['bbox'].find(f'{{*}}UpperCorner', namespaces=self.__namespace).text.split()[1])]
            else:
                feature['bbox'] = feature_type.find(f'{{*}}LatLongBoundingBox', namespaces=self.__namespace)
                if feature['bbox'] is not None:
                    feature['bbox'] = [float(feature['bbox'].attrib['minx']),
                                       float(feature['bbox'].attrib['miny']),
                                       float(feature['bbox'].attrib['maxx']),
                                       float(feature['bbox'].attrib['maxy'])]
                else:
                    if feature['bbox'] is None:
                        try:
                            xMin = feature.find('.//{*}LowerCorner').text.split(' ')[0]
                            yMin = feature.find('.//{*}LowerCorner').text.split(' ')[1]
                            xMax = feature.find('.//{*}UpperCorner').text.split(' ')[0]
                            yMax = feature.find('.//{*}UpperCorner').text.split(' ')[1]
                            feature['bbox'] = [float(xMin), float(yMin), float(xMax), float(yMax)]
                        except:
                            feature['bbox'] = None
            feature_list[feature['name'].split(':')[-1]] = feature
            
        return feature_list

    def __get_operations(self):
        """
        Get the list of operations from the WFS service.
        """
        operations = {}
        if self.version >= '2.0.0':
            for operation in self.get_capabilities_root.findall(f'.//{{*}}Operation', namespaces=self.__namespace):
                op_name = operation.attrib['name']
                operations[op_name] = {}
                parameters = {}
                for parameter in operation.findall(f'{{*}}Parameter', namespaces=self.__namespace):
                    name = parameter.attrib['name']
                    # parameters[name] = {}
                    AllowedValues = parameter.find(f'{{*}}AllowedValues', namespaces=self.__namespace)
                    if AllowedValues is not None:
                        values = AllowedValues.findall(f'{{*}}Value', namespaces=self.__namespace)
                        if values is not None:
                            parameters[name] = [value.text for value in values]
                operations[op_name]['parameters'] = parameters
            return operations
        elif self.version < '2.0.0':
            for item in self.get_capabilities_root.findall(f'.//{{*}}Request', namespaces=self.__namespace):
                for req in item:
                    op_name = req.tag.split('}')[-1]
                    operations[op_name] = {}
            return operations
        else:
            return None                  
        
    def __clip_gdf(self, tmp_gdf):
        """
        Klipper en GeoDataFrame til bounding box defineret i WFS-objektet.
        
        Parametre:
            gdf (GeoDataFrame): GeoDataFrame der skal klippes
            
        Returnerer:
            GeoDataFrame: Klippet GeoDataFrame
        """
        # tmp_gdf = gdf.copy()
        # tmp_gdf.crs = "EPSG:4326"
        # tmp_gdf = tmp_gdf.to_crs("EPSG:25832")
        gdf_bbox = box(float(self.__default_bbox[0]), float(self.__default_bbox[1]), float(self.__default_bbox[2]), float(self.__default_bbox[3]))
        gdf_bbox = gpd.GeoDataFrame({'geometry': [gdf_bbox]})
        gdf_bbox.crs = "EPSG:25832"
        try:
            tmp_gdf.set_crs("EPSG:25832", inplace=True)
            tmp_gdf = tmp_gdf.to_crs("EPSG:25832")
        except Exception as e:
            if self.__debug: print(e)
            pass
        if self.__debug:
            print('Clipping GeoDataFrame to bounding box')
            print(float(self.__default_bbox[0]), float(self.__default_bbox[1]), float(self.__default_bbox[2]), float(self.__default_bbox[3]))
            print(tmp_gdf.crs)
            print(gdf_bbox.crs)
        try:
            gdf = tmp_gdf.clip(gdf_bbox)
        except Exception as e:
            if self.__debug: print('Error clipping GeoDataFrame:', e)
            gdf = tmp_gdf
        if self.__debug: print('Clipped GeoDataFrame:')
        return gdf
    
    def __descripe_feature(self, feature_name):
        """
        Henter metadata for et specifikt feature lag fra WFS-tjenesten.
        
        Funktionen danner en WFS GetFeature forespørgsel med resulttype=describeFeature
        og returnerer metadata som en GeoDataFrame.
        
        Parametre:
            feature_name (str): Navnet på det ønskede feature lag
            
        Returnerer:
            GeoDataFrame: GeoDataFrame med metadata for det specifikke feature lag
            
        Raises:
            ValueError: Hvis GeoDataFrame ikke kan læses fra WFS-responsen
        """
        if self.__debug: print('Getting DescribeFeatureType')
        params = self.__params
        params['request'] = 'DescribeFeatureType'
        params['version'] = self.version
        params['typeNames'] = feature_name
        
        if self.__debug: print('params:', params)
        wfs_url = requests.Request('GET', self.url, params=params).prepare().url
        if self.__debug: 
            print('Getting DescribeFeatureType')
            print(wfs_url)
        with_username_password = True
        response = requests.get(wfs_url, auth=(self.username, self.password) if self.username and self.password else None)
        if response.status_code != 200:
            if self.__debug: print('Authentication failed, trying without authentication')
            response = requests.get(wfs_url)
            with_username_password = False
        root = etree.XML(response.content)
        ns = root.nsmap
        ints = []
        decimals = []
        datetimes = []
        fc_schema = []
        for e in root.findall(f'.//{{*}}complexContent//{{*}}element', namespaces=ns):
            e = e.attrib
            dtype = e['type']
            # if self.__debug: print(f'Element: {e} - Type: {dtype}')
            if 'int' in dtype.lower():
                ints.append(e['name'])
            elif 'decimal' in dtype.lower():
                decimals.append(e['name'])
            elif 'date' in dtype.lower():
                datetimes.append(e['name'])
            else:
                fc_schema.append(e['name'])
        # if self.__debug: print(f'ints: {ints} - decimals: {decimals} - datetimes: {datetimes} - fc_schema: {fc_schema}')
        return {'ints':ints, 'decimals':decimals, 'datetimes':datetimes, 'fc_schema':fc_schema}


    def __get_feature(self, feature_name, bbox, filter=None):
        gdfs = []
        params = self.__params.copy()
        params.update({
            'resulttype': 'results',
            'request': 'GetFeature',
            'bbox': ','.join(bbox),
            'version': self.version
        })
        if self.__paging:
            params['startindex'] = '0'
        params['typeNames'] = feature_name

        if 'cql_filter' in params.keys():
            del params['bbox']

        if filter:
            filter = "".join(filter.splitlines())
            # Remove bbox from params when using filter
            if 'bbox' in params.keys():
                del params['bbox']

        wfs_url = requests.Request('GET', self.url, params=params).prepare().url
        if filter:
            wfs_url += f'&filter={filter}'
        if self.__debug: 
            print('wfs_url', wfs_url)
        if self.__logger:
            self.__logger.info(f'WFS GetFeature URL: {wfs_url}')

        tries = 5
        while tries > 0:
            try:
                result = requests.get(wfs_url, auth=(self.username, self.password) if self.username and self.password else None)
                if '<ows:Exception exceptionCode="NoApplicableCode">' in result.text:
                    raise Exception('WFS GetFeature returned NoApplicableCode exception')
                if self.__logger:
                    self.__logger.info(f'WFS GetFeature request successful on try {6 - tries}')
                break
            except Exception as e:
                tries -= 1
                if self.__debug: print(f'Error fetching WFS GetFeature: {e}, tries left: {tries}')
                if self.__logger:
                    self.__logger.info(f'Error fetching WFS GetFeature: {e}, tries left: {tries}')
                if tries == 0:
                    raise Exception(f'Could not fetch WFS GetFeature after multiple tries: {e}')
        with_username_password = True
        # if self.__debug:
        #     print('result', result.text)
        if result.status_code != 200:
            if self.__debug: print('Authentication failed, trying without authentication')
            result = requests.get(wfs_url)
            with_username_password = False
        if self.__debug:
            print('___get_features_gdf after auth try', with_username_password)
            print('Status code:', result.status_code)
            self.spec_resp = result
            # print('Response text:', result.text)

        ## test if numberMatched="0" numberReturned="0" in result
        root = etree.XML(result.content)
        if 'numberMatched' in root.attrib.keys():
            if root.attrib['numberMatched'] == '0' and root.attrib['numberReturned'] == '0':
                if self.__debug: print('No features found in WFS response')
                if self.__logger:
                    self.__logger.info('No features found in WFS response')
                return gdfs
        try:
            if self.__logger:
                self.__logger.info('Reading GeoDataFrame from WFS response with StringIO')
            gdf = gpd.read_file(StringIO(result.text))
        except Exception as e:
            if self.__logger:
                self.__logger.info(f'Reading GeoDataFrame from WFS response with content due to error: {e}')
            try:
                self.__logger.info('Reading GeoDataFrame from WFS response with content')
                gdf = gpd.read_file(result.content)
                self.__logger.info(f'GeoDataFrame read successfully from WFS response content: {len(gdf)} features')
            except Exception as e:
                if self.__debug: print(f'Could not read GeoDataFrame from WFS response: {e}')
                if self.__logger:
                    self.__logger.critical(f'Could not read GeoDataFrame from WFS response: {e}')
                raise Exception(f'Could not read GeoDataFrame from WFS response: {e}')
        ## check if theres a attribute named 'next' in the response to handle paging
        try:
            gdf.set_crs("EPSG:25832", inplace=True, allow_override=True)
            gdfs.append(gdf)
        except Exception as e:
            if self.__debug: print(f'Could not read GeoDataFrame from WFS response: {e}')
            if self.__logger:
                self.__logger.error(f'Could not read GeoDataFrame from WFS response: {e}')
            raise Exception(f'Could not read GeoDataFrame from WFS response: {e}')
        def get_next_url(result):
            root = None
            try:
                root = etree.XML(result.content)
                ns = root.nsmap
                if 'next' in root.attrib.keys():
                    _next_url = root.attrib['next']
                    if self.__debug: print('Paging detected, next url:', _next_url)
                    if self.__logger:
                        self.__logger.info(f'Paging detected, next url: {_next_url}')
                    return _next_url
                else:
                    _next_url = None
                    return _next_url
            except Exception as e:
                if self.__debug: print(f'Could not parse paging information: {e}')
                _next_url = None
                return _next_url
        next_url = get_next_url(result)

        while next_url:
            if self.__debug: print('Fetching next page:', next_url)
            if with_username_password:
                tries = 5
                while tries > 0:
                    try:
                        result = requests.get(next_url, auth=(self.username, self.password) if self.username and self.password else None)
                        if '<ows:Exception exceptionCode="NoApplicableCode">' in result.text:
                            raise Exception('WFS GetFeature returned NoApplicableCode exception')
                        if self.__logger:
                            self.__logger.info(f'WFS GetFeature paging request successful on try {6 - tries}')
                        break
                    except Exception as e:
                        tries -= 1
                        if self.__debug: print(f'Error fetching WFS GetFeature page: {e}, tries left: {tries}')
                        if self.__logger:
                            self.__logger.info(f'Error fetching WFS GetFeature page: {e}, tries left: {tries}')
                        if tries == 0:
                            raise Exception(f'Could not fetch WFS GetFeature page after multiple tries: {e}')
                # result = requests.get(next_url, auth=(self.username, self.password) if self.username and self.password else None)
            else:
                tries = 5
                while tries > 0:
                    try:
                        result = requests.get(next_url)
                        if '<ows:Exception exceptionCode="NoApplicableCode">' in result.text:
                            raise Exception('WFS GetFeature returned NoApplicableCode exception')
                        if self.__logger:
                            self.__logger.info(f'WFS GetFeature paging request successful on try {6 - tries}')
                        break
                    except Exception as e:
                        tries -= 1
                        if self.__debug: print(f'Error fetching WFS GetFeature page: {e}, tries left: {tries}')
                        if self.__logger:
                            self.__logger.info(f'Error fetching WFS GetFeature page: {e}, tries left: {tries}')
                        if tries == 0:
                            raise Exception(f'Could not fetch WFS GetFeature page after multiple tries: {e}')
                # result = requests.get(next_url)
            try:
                if self.__logger:
                    self.__logger.info('Reading GeoDataFrame from WFS paging response with StringIO')
                gdf = gpd.read_file(StringIO(result.text))
            except Exception as e:
                if self.__logger:
                    self.__logger.info(f'Reading GeoDataFrame from WFS paging response with content due to error: {e}')
                try:
                    gdf = gpd.read_file(result.content)
                except Exception as e:
                    if self.__debug: print(f'Could not read GeoDataFrame from WFS paging response: {e}')
                    if self.__logger:
                        self.__logger.critical(f'Could not read GeoDataFrame from WFS paging response: {e}')
                    raise Exception(f'Could not read GeoDataFrame from WFS paging response: {e}')
            gdf.set_crs("EPSG:25832", inplace=True, allow_override=True)
            gdfs.append(gdf)
            next_url = get_next_url(result)

        if self.__logger:
            self.__logger.info(f'Returning {len(gdfs)} GeoDataFrames from WFS GetFeature')
        return gdfs        

    def get_features(self, feature_name, **kvargs):
        """
        Hent features fra et WFS lag.

        Funktionen laver en WFS GetFeature forespørgsel og returnerer data som GeoDataFrame.
        Den håndterer automatisk opdeling i mindre bbox'e, hvis der er for mange features.

        Parametre:
            feature_name (str): Navn på det ønskede WFS lag
            **kvargs: Ekstra parametre der tilføjes WFS forespørgslen
            clip_gdf (bool, optional): Hvis True, klippes GeoDataFrame til bbox defineret i WFS-objektet
            filter (str, optional): Filter til WFS forespørgslen
            raw_dates (bool, optional): Hvis True, returneres datoer som strenge i stedet for datetime objekter
                
        Returnerer:
            GeoDataFrame: GeoDataFrame med features fra WFS laget
            
        Raises:
            ValueError: Hvis GeoDataFrame ikke kan læses fra WFS responsen
        """
        for key, value in kvargs.items():
            setattr(self, key, value)
        
        ## check if clip_gdf is set
        if hasattr(self, 'clip_gdf'):
            clip_gdf = self.clip_gdf
        else:
            clip_gdf = True

        if hasattr(self, 'filter'):
            filter = self.filter
        else:
            filter = None

        if hasattr(self, 'raw_dates'):
            self.raw_dates = self.raw_dates
        else:
            self.raw_dates = False

        if self.bboxes is None:
            self.bboxes = [[str(b) for b in self.feature_list[feature_name]['bbox']]]
            self.__default_bbox = self.bboxes[0]

        bboxes = self.bboxes.copy()
        if self.__debug: print(f'Bounding boxes: {self.bboxes}')
        gdfs = []
        gdf = None
        for bbox in bboxes:
            if self.__debug: print(f'Bounding box: {bbox}')
            
            gdfs = self.__get_feature(feature_name, bbox)
            

        if len(gdfs) == 0:
            raise ValueError('No features found in WFS response')
        self.gdfs = gdfs
        gdf = pd.concat(gdfs, ignore_index=True)
        if self.__debug: print(f'Number of features: {len(gdf)}')
        if self.__logger:
            self.__logger.info(f'Number of features retrieved: {len(gdf)}')
        gdf.drop_duplicates(inplace=True)
        # for col in gdf.columns.to_list():
        if self.__debug:
            print("Original columns:", gdf.columns.to_list())
        gdf.rename(columns={col: col.replace('.', '_').replace('-', '_') for col in gdf.columns}, inplace=True)
        if self.__debug:
            print("Renamed columns:", gdf.columns.to_list())

        gdf['xTid'] = pd.Timestamp.now()
        if clip_gdf and len(gdf) > 0:
            gdf = self.__clip_gdf(gdf)
            if self.__logger:
                self.__logger.info(f'GeoDataFrame clipped to bounding box: {self.__default_bbox}')

        
        return gdf
