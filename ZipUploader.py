'''
Script to zip a provided file or folder and send it to a ftp server
Submission by Owen Harbert

This was a fun challenge, thankfully I'm not as rusty in Python as I thought I was.
I did do some studying and practice before attempting this script just so I could
use my time as efficiently as possible and while I definitely overscoped what I
would manage I'm very happy with what I was able to get done in the time and will 
probably complete it in a copy of this file in my own time.
Another thing is you'll likely see some pracitices I carry over from C# even if 
I don't realise them, I've tried to keep variables and functions named with python
coding conventions but there are places I likely slipped up there.

I made use of the following ftp details for testing:
host:       ftp.dlptest.com
user:       dlpuser
password:   rNrKYTX9g7z3RgJRmxWuGHbeu

A few more features I would add:
-   Checking if a file/s have already been sent as we don't want the server filling up with 
    duplicates.
-   As I described below, a way to display progress of the zipping and uploading processes,
    preferably with some sort of configurable loading bar.
-   A couple test functions so I don't have to type things out everytime I want to test for
    further develepment. But that's just for lazy people...
-   The ability to save FTP info, if we're only ever using the same 1 or more FTP servers
    then saving the credentials so that it can be quickly loaded would be very convenient.
-   Move the logging methods into a seperate module and just import it (just found out 
    that there is already a logging package and bravo me for not having a better look)
-   Finally I'd like to reorganise the script so that it can be run multiple times.

NOTE: Running the file in terminal, command prompt and IDE is successful but whenever I try 
double clicking it, the file just seems to close for what I assume is the os module. 
So when trying it out just use cmd, an IDE or your preferred terminal.
'''

import os
import pathlib
import datetime
import ftplib
import pyminizip as zipper

# date and time used for logging and naming
def get_current_time() -> str:
    current_time: str = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M")
    return current_time

# name of log file for this session
log_name: str = f"log_{get_current_time()}.log"

# basically a print statement that logs the text
def print_log(text: str):
    log(text)
    print(text)

# raises exception error and prints it
def raise_log(text: str):
    log(f"Error: {text}")
    raise Exception(text)

# log any print statements to a log file
def log(text: str):
    date_time = datetime.datetime.now()
    logs: str = os.path.join(os.getcwd(), "Logs")
    
    # make logs folder if it does not exist
    if not os.path.exists(logs):
        os.makedirs(logs)
    
    file = open(os.path.join(logs, log_name), 'a')
    file.write(f'\n{date_time.strftime("%Y/%m/%d, %H:%M:%S")}: {text}')
    file.close

# process and return valid path
def get_path(path: str) -> str:
    # process the raw string and return a valid path
    path = path.strip("& '\"")
    path = pathlib.PurePath(path).as_posix()

    print_log(f"User entered: {path}")

    # verify path is valid
    if not os.path.exists(path):
        raise_log(f"{path} does not exist or path is invalid")

    cont = input(f"Conifirm {os.path.basename(path)} is the file/folder you wish to zip (y/n): ")

    if cont.lower() == "y":
        return path
    else:
        print_log("Program cancelled by user.")
        quit()
    # I should have included checks like this for the zip and login steps

# find files to send
def get_files(path: str) -> str | list[str]:
    # if path is a file return path
    print_log("Files to Zip:")

    if os.path.isfile(path):
        print_log(os.path.basename(path))
        return path
    
    # else return list of files
    fileList: list[str] = os.listdir(path)
    toZip: list[str] = []
    
    # add files to toZip list excluding subfolders due to time constraints
    for file in fileList:
        if os.path.isfile(os.path.join(path, file)):
            # add full path to each item
            filePath = os.path.join(path, file)
            toZip.append(filePath)

    # print a list of the files to be zipped
    count: int = 0
    for file in toZip:
        count += 1
        print_log(f"{count}. {os.path.basename(file)}")

    return toZip

# zip the files
def zip_files(files: str | list[str], outputDir: str, password: str, compression_lvl: int = 0) -> str:
    # add zip file name to directory
    zipName: str = "Package_" + get_current_time() + ".zip"
    output: str = os.path.join(outputDir, zipName)
    
    print_log("Zipping Files...")

    if isinstance(files, list):
        # zip multiple files
        zipper.compress_multiple(files, [], output, password, compression_lvl)
    else:
        # zip just a single file
        zipper.compress(files, None, output, password, compression_lvl)
    
    print_log(f"{os.path.basename(output)} compressed in {outputDir}")
    return output

# 
def set_password() -> str:
    attempts = 3
    
    # if passwords don't match then retry
    while attempts > 0:
        zipPassword: str = input("Enter zip file password: ")
        confirmPassword: str = input("Confirm zip file password: ")

        if zipPassword == confirmPassword:
            print_log("Password Set Successfully")
            return zipPassword
        else: 
            print_log("Values do not match! Try Again")
            attempts -= 1

    raise_log("Password attempts exceeded")

# send to ftp server
def login_to_server() -> ftplib.FTP:
    # Login to FTP Server
    # If you accidentally press enter when it is empty retry
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

            print_log(f"Connected to {host}")
            return session
        except ftplib.all_errors as e:
            # if fail to connect ask if the user wants to try again else quit
            print_log(f"Incorrect server details: {e}")

            retry: str = input("Do you want to retry? (y/n): ")

            if retry.lower() != "y":
                print_log("FTP login failed.")
                quit()
            else:
                continue

def upload(zipFile: str, session: ftplib.FTP) -> None:
    file = open(zipFile, "rb")

    zipFileName = os.path.basename(zipFile)

    print_log(f"Uploading {zipFileName}...")

    # change Dir to a recieve folder
    try:
        session.cwd("Recieved")
    except:
        session.mkd("Recieved")
        session.cwd("Recieved")

    # send the zip file to the server
    session.storbinary("STOR " + zipFileName, file)
    
    '''NOTE: The storbinary function has a callback that could be used to see the progress
    of the upload and I would like to implement this as a feature in future a similar
    method exists for the zip compression method'''

    if validate_succesful_upload(session, zipFile, zipFileName):
        print_log(f"{zipFileName} Uploaded Successfully!")
        # I'd also like to display the number of seconds that have passed when uploaded
    else:
        raise_log(f"{zipFileName} Upload Failed or Corrupted")

    file.close()
    
def validate_succesful_upload(session: ftplib.FTP, zipFile: str, fileOnServer: str) -> bool:
    serverSize = session.size(fileOnServer)
    localSize = pathlib.Path(zipFile).stat().st_size

    print_log(f"file size on server: {serverSize}")
    print_log(f"file size on machine: {localSize}")

    if serverSize == localSize:
        return True
    else:
        return False

def main() -> None:
    # INITIALIZE
    # output folder made in the working directory
    # used to store zip files before sending
    depot: str = os.path.join(os.getcwd(), "Depot")
    
    # make output folder if it does not exist
    if not os.path.exists(depot):
        os.makedirs(depot)
    
    # GET FILE/S
    # prompt user to drag a file/folder or type/paste an address
    rawInputPath: str = input("Enter File Path: ")
    # path post process
    inputPath: str = get_path(rawInputPath)
    
    # get list/string of files to send
    files: str | list[str] = get_files(inputPath)

    # ZIP FILE/S
    password: str = set_password()
    zipFile: str = zip_files(files, depot, password)

    # LOGIN TO SERVER
    session = login_to_server()

    # UPLOAD TO SERVER
    upload(zipFile, session)

    input("Press Anything to finish")

if __name__ == "__main__":

    main()
