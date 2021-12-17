# console.py
"""Helper module for terminal verbosity and commands
"""
import subprocess
import logging

class Console:
    """shell wrapper"""
    __logger = None
    @staticmethod
    def __init__(loglevel=logging.WARN):
        """constructor, set up logging including extra loglevel"""
        logging.TRACE = 5
        logging.addLevelName(5, "TRACE")
        Console.__logger = logging.getLogger('console')
        setattr(Console.__logger, 'trace',
                lambda *args: Console.__logger.log(5, *args))

        log_handler = logging.StreamHandler()
        log_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        Console.__logger.addHandler(log_handler)
        Console.__logger.setLevel(loglevel)

    @staticmethod
    def run(command, pwd=None, return_stderr=False):
        """run shell command
        Args:
            command (str): command to execute
            pwd (str, optional): directory to execute in
            return_stderr (bool, optional): include stderr in return value if set to true
        Returns:
            str: command output
        """
        if not Console.__logger:
            Console.__init__()
        if pwd:
            command = 'cd ' + pwd + ' && ' + command
        Console.__logger.debug("Running command %s", command)
        result = subprocess.run(command, capture_output=True, shell=True,
                                check=False)
        for line in result.stdout.decode('utf-8').splitlines():
            Console.__logger.debug(line)
        for line in result.stderr.decode('utf-8').splitlines():
            Console.__logger.warning(line)
        if return_stderr:
            return (result.stdout.decode('utf-8'),
                    result.stderr.decode('utf-8'))
        return result.stdout.decode('utf-8')

    @staticmethod
    def set_log_level(loglevel):
        """set loglevel
        Args:
            loglevel (int): loglevel to set
        """
        if not Console.__logger:
            Console.__init__()
        Console.__logger.setLevel(loglevel)
