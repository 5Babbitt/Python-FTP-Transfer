'''
Script to zip a provided file or folder and send it to a ftp server

I made use of the following ftp details for testing:
host:       ftp.dlptest.com
user:       dlpuser
password:   rNrKYTX9g7z3RgJRmxWuGHbeu

A few more features I would add:
-   Checking if a file/s have already been sent as we don't want the server filling up with 
    duplicates.
-   A couple test functions so I don't have to type things out everytime I want to test for
    further develepment. But that's just for lazy people...
-   Include subfolders

NOTE: Running the file in terminal, command prompt and IDE is successful but whenever I try 
double clicking it, the file just seems to close for what I assume is the os moduleuse. 
So when trying it out just use cmd, an IDE or your preferred terminal.
'''

import os
import sys
import pathlib
import ftplib
import pyminizip as zipper
from TimeUtils import get_current_time
from LogUtils import print_log, raise_log, initialize_log

def init() -> None:
    '''Initialize program paths, setting working dir to this scripts path'''
    abspath = os.path.abspath(__file__)
    dname = os.path.dirname(abspath)
    os.chdir(dname)
    print(f'Working directory: {os.getcwd()}')

def print_progress_bar (iteration: int, total: int, prefix: str = '', suffix: str = '',
                      decimals: int = 1, length: str = 100, fill: str = '█',
                      print_end: str = "\r") -> None:
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        print_end    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    progress_bar = fill * filled_length + '-' * (length - filled_length)

    print(f'\r{prefix} |{progress_bar}| {percent}% {suffix}', end = print_end)
    # Print New Line on Complete
    if iteration == total:
        print()

def prompt(text: str) -> bool:
    '''Reusable prompt for continuing loops'''
    cont: str = input(f"{text} (y/n): ")
    if cont.lower() == "y":
        return True

    return False

def get_output() -> str:
    '''Return the output folder, if it does not exist make it'''
    depot: str = os.path.join(os.getcwd(), "Depot")
    os.makedirs(depot, exist_ok=True)

    return depot

def get_path() -> str:
    '''process the raw string and return a valid path'''
    input_path: str  = input("Enter File Path: ")
    # remove forbidden characters and format correctly
    path: str = pathlib.PurePath(input_path.strip(" &'\"<>:|?*.")).as_posix()

    print_log(f"Path entered: {path}")

    # verify path is valid
    if not os.path.exists(path):
        raise_log(f"{path} does not exist or path is invalid")

    if prompt(f"Conifirm {os.path.basename(path)} is the file/folder you wish to zip?"):
        return path
    
    print_log("Program cancelled by user.", is_debug=True)
    sys.exit()

def get_files() -> list[str]:
    '''Find and return the file(s) to zip'''
    print_log("Files to Zip:")

    path: str = get_path()

    # if the path is already a file then return that path
    if os.path.isfile(path):
        print_log(f"1. {os.path.basename(path)}")
        return [path]

    # else return a list of the files
    to_zip: list[str] = [os.path.join(path, file) for file in os.listdir(path)
                        if os.path.isfile(os.path.join(path, file))]

    # print a list of the files to be zipped
    for count, file in enumerate(to_zip, start=1):
        print_log(f"{count}. {os.path.basename(file)}")

    return to_zip

def zip_files(files: list[str], output_dir: str, password: str,
              compression_lvl: int = 9) -> str:
    '''Zip them files.'''

    # add zip file name to directory
    zip_name: str = "Package_" + get_current_time() + ".zip"
    output: str = os.path.join(output_dir, zip_name)

    print_log("Zipping Files...")

    def zip_progress(zipped): print_progress_bar(zipped, len(files), prefix="Zipped:   ")

    try:
        zipper.compress_multiple(files, [], output, password, compression_lvl, zip_progress)
    except Exception as e:
        raise_log(f"Error occured while zipping files: {e}")

    print_log(f"{os.path.basename(output)} compressed in {output_dir}")

    return output

def set_password() -> str:
    '''Give the user 3 attempts to set a valid password and return it'''
    attempts = 3

    # if passwords don't match then retry
    while attempts > 0:
        zip_password: str = input("Enter zip file password: ")
        confirm_password: str = input("Confirm zip file password: ")

        if zip_password == confirm_password:
            print_log("Password Set Successfully")
            return zip_password

        print_log("Values do not match! Try Again")
        attempts -= 1

    raise_log("Password attempts exceeded")

def login_to_server() -> ftplib.FTP:
    '''Login to FTP server and return the client class'''
    while True:
        host = input("Enter FTP Host: ")
        user = input("Enter FTP Username: ")
        password = input("Enter FTP Password: ")

        # if an item is empty then retry
        if not host or not user or not password:
            print_log("Empty Credentials! Retry")
            continue

        try:
            print_log("Connecting...")

            session = ftplib.FTP(host, user, password)

            print_log(f"Connected to {host} as {user}")
            return session
        except ftplib.all_errors as e:
            # if fail to connect ask if the user wants to try again else quit
            print_log(f"Connection Failed: {e}", is_error=True)

            if prompt("Do you want to retry?"):
                continue

            print_log("FTP login failed.")
            quit()

def upload(zip_file: str, session: ftplib.FTP) -> None:
    '''Upload Zip file to FTP server'''
    file = open(zip_file, "rb")
    zip_size = pathlib.Path(zip_file).stat().st_size

    zip_file_name = os.path.basename(zip_file)

    print_log(f"Uploading {zip_file_name}...")

    # set correct working directory
    if session.pwd != "Recieved":
        try:
            session.cwd("Recieved")
        except Exception:
            session.mkd("Recieved")
            session.cwd("Recieved")

    def upload_progress(progress):
        upload_progress.sent += len(progress)
        print_progress_bar(upload_progress.sent, zip_size, prefix="Uploaded: ")
    upload_progress.sent = 0

    # send the zip file to the server
    session.storbinary("STOR " + zip_file_name, file, callback=upload_progress)

    if validate_succesful_upload(session, zip_file, zip_file_name):
        print_log(f"{zip_file_name} Uploaded Successfully!")
    else:
        raise_log(f"{zip_file_name} Upload Failed or Corrupted")

    file.close()

def validate_succesful_upload(session: ftplib.FTP, zip_file: str, server_file: str) -> bool:
    '''Compare file size between server and machine to validate successful upload'''
    server_size = session.size(server_file)
    local_size = pathlib.Path(zip_file).stat().st_size

    print_log(f"file size on server: {server_size}", is_debug=True)
    print_log(f"file size on machine: {local_size}", is_debug=True)

    if server_size == local_size:
        return True
    else:
        return False

def main() -> None:
    '''Main program operations'''
    while True:
        # INITIALIZE
        initialize_log()
        # LOGIN TO SERVER
        session = login_to_server()

        while True:
            zip_file: str = zip_files(get_files(), get_output(), set_password())
            upload(zip_file, session)

            # prompt if user woould like to send more files to the same server
            if prompt(f"Would you like to upload more files to {session.host}?"):
                continue
            break

        if prompt("Would you like to upload more files to another server?"):
            continue

        break

    print_log("Exited Session")

if __name__ == "__main__":
    init()
    main()
