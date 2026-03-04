from logger.logger import Logger 
# import os
# print(os.getcwd())

if __name__ == "__main__":
    log = Logger(debug=False, print_msg=False)
    log.start()
    log.stars('Dette er en stjernebesked', num=5)
    log.info('Dette er en informationsbesked')
    log.warning('Dette er en advarselsbesked')
    log.error('Dette er en fejlbesked')
    log.critical('Dette er en kritisk besked')
    log.end()