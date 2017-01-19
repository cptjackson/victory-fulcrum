import sys
import imaplib
import getpass
import email
import pickle
from time import mktime
from datetime import *
from dateutil.parser import *
import requests
import calendar


def main():

    jobsLoaded = False
    exitProg = False
    curr = 'CAD'

    # Print options
    print('Editing database manager v. 0.0.4')

    while not exitProg:
    
        print('\nChoose your option:')
        print('1: scan for new messages')
        print('2: save job list')
        print('3: load job list')
        print('4: print current job list')
        print('5: clear current job list')
        print('6: financial options')
        print('7: generate invoice')
        print('8: quit')

        choice = input('What do you want to do? ')
        if choice == '1':

            # Clear current list
            jobDict = {}

            # Input email
            address = input('Enter email: ')
            
            # Scan for messages
            msgList = getMessages(address)

            if msgList != None:

                # Now parse those emails and build the job list
                for msg in msgList:

                    job = parse_mail(msg)

                    addJob(jobDict, job)
                    
                jobsLoaded = True
                
        elif choice == '2':

            if not jobsLoaded:
                print('ERROR: No job list loaded.')
            else:
                # Save job list
                saveJobDict(jobDict,'jobdata.pkl')
                print('Job list saved.')
            
        elif choice == '3':

            # Load job list
            jobDict = loadJobDict('jobdata.pkl')
            jobsLoaded = True
            print('Job list loaded.')

        elif choice == '4':

            if not jobsLoaded:
                print('ERROR: No job list loaded.')
            else:
                # Print job list
                for name,job in jobDict.items():
                    print('\n')
                    print(job)
                    
        elif choice == '5':

            jobDict = {}
            jobsLoaded = False
            print('Job list cleared.')

        elif choice == '6':

            if not jobsLoaded:
                print('ERROR: No job list loaded.')
            else:

                exitFinance = False

                while not exitFinance:

                    # Get conversion rates
                    url = ('https://currency-api.appspot.com/api/%s/%s.json') % ('JPY', 'CAD')
                    r = requests.get(url)
                    yenRate = float(r.json()['rate'])
                    url = ('https://currency-api.appspot.com/api/%s/%s.json') % ('RMB', 'CAD')
                    r = requests.get(url)
                    rmbRate = float(r.json()['rate'])
                    url = ('https://currency-api.appspot.com/api/%s/%s.json') % ('USD', 'CAD')
                    r = requests.get(url)
                    usdRate = float(r.json()['rate'])
                    rates = [yenRate, rmbRate, usdRate]

                    print('\nFinance options')
                    print('Current currency:',curr)
                    print('1: print total income')
                    print('2: print monthly income')
                    print('3: change currency')
                    print('4: return to main menu')
                    print('5: quit')

                    choice = input('What do you want to do? ')

                    if choice == '1':

                        # Add up income
                        totalIncome = 0
                        for name,job in jobDict.items():
                            totalIncome += job.get_fee(rates)                                              

                        print('Total income: ${:.2f}'.format(totalIncome))

                    elif choice == '2':

                        # First go through and snag all different dates
                        dateList = []
                        for name,job in jobDict.items():
                            aDate = job.assignDate
                            
                            if aDate.month not in dateList:
                                dateList.append(aDate.month)

                        # Sort list by date
                        dateList.sort()

                        # Now go through each month
                        incomeByDate = {}
                        for d in dateList:
                            incomeByDate[d] = 0
                            for name,job in jobDict.items():
                                if job.assignDate.month == d:
                                    incomeByDate[d] += job.get_fee(rates)

                        # Finally print income by date
                        for d,val in incomeByDate.items():
    
                            print('{}: ${:.2f}'.format(calendar.month_name[d], val))
                                    

                    elif choice == '3':

                        print('Change currency to what?')
                        

                    elif choice == '4':

                        print('Heading back to main menu...')
                        exitFinance = True

                    elif choice == '5':

                        print('Bye!')
                        exitFinance = True
                        exitProg = True

                    else:
                        print('ERROR: Input not recognised. Try again.')

        elif choice == '7':

            

        elif choice == '8':

            print('Bye!')
            exitProg = True
            
        else:
            print('ERROR: Input not recognised. Try again.')

    # We're done here!
    sys.exit()


def addJob(jobs, job):

    # check if job is already in dict
    if job.name not in jobs:

        jobs[job.name] = job
   
    
# Given a list of Job objects and a filename, pickle the list to a binary file.
def saveJobDict(jobs,fname):

    f = open(fname, 'wb')

    pickle.dump(jobs, f, -1)
          
    f.close()


# Given a filename, unpickle a list of Job objects from a binary file and return it.
def loadJobDict(fname):

    f = open(fname, 'rb')

    jobs = pickle.load(f)
          
    f.close()

    return jobs


# Log in to email server and get messages (new jobs only in last two weeks)
def getMessages(address):

    msgList = []

    # Log in to email
    M = imaplib.IMAP4_SSL('imap.gmail.com')

    try:
        M.login(address, getpass.getpass())
    except imaplib.IMAP4.error:
        print("Login failed.")
        return None

    # Select Editing mailbox
    rv, data = M.select("Editing")
    if rv == 'OK':

        # Format date correctly    
        searchDate = date.today()-timedelta(days=19)
        searchDate = searchDate.strftime('%d-%b-%Y')

        # Pull emails in date range
        print("Attempting to pull emails...")
        rv, data = M.search(None, "SINCE " + searchDate)
        if rv != 'OK':
            print("No messages found.")
        else:
            print("Success!")

            # Build the message list, new jobs only
            for num in data[0].split():
                rv, data = M.fetch(num, '(RFC822)')
                if rv != 'OK':
                    print("ERROR getting message", num)

                msg = email.message_from_bytes(data[0][1])

                if "New Job - 1st Edit" in msg['Subject']: # and "Rev" not in msg['Subject']:
                    msgList.append(msg)

        M.close()
    M.logout()

    return msgList


# ok let's see what we need to do
# check email every n hours
# search through email for correct mails - DONE
# search through mails for correct info - DONE
# plonk info into database
# set up UX to give tags and notes etc


# unused
def decode_mail(msg):

    text = ""
    if msg.is_multipart():
        html = None
        for part in msg.get_payload():

            print("%s, %s" % (part.get_content_type(), part.get_content_charset()))

            if part.get_content_charset() is None:
                # We cannot know the character set, so return decoded "something"
                text = part.get_payload(decode=True)
                continue

            charset = part.get_content_charset()

            if part.get_content_type() == 'text/plain':
                text = str(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

            if part.get_content_type() == 'text/html':
                html = str(part.get_payload(decode=True), str(charset), "ignore").encode('utf8', 'replace')

        if text is not None:
            return text.strip()
        else:
            return html.strip()
    else:
        text = str(msg.get_payload(decode=True), msg.get_content_charset(), 'ignore').encode('utf8', 'replace')
        return text.strip()


# Parse an email message
def parse_mail(msg):

    # Get mail text and date
    mail_text = msg.get_payload(decode=True).splitlines()
    mail_date = datetime.fromtimestamp(mktime(email.utils.parsedate(msg['Date'])))
    job_done = False

    # Find job name and instantiate Job object
    for l in mail_text:

        line = l.decode("utf-8")

        if 'Name:' in line:

            job = Job(line[6:],mail_date)
            job_done = True
            
            break

    # Now go through and add the rest of the data
    if job_done:

        # Initialise a few things
        num_pages = 0
        fee = 0
        links = []
        do_refs = False
        do_tabs = False
        do_figs = False
        message_running = False
        message = ""

        for index, l in enumerate(mail_text):

            line = l.decode("utf-8")

            # Start with figuring out if we've hit the message yet
            if '***' in line and 'Message' in line:

                if not message_running:
                    message_running = True

            # Only do the following if we are outside the message range
            if not message_running:

                if 'Stage:' in line:

                    job.add_stage(line[7:])

                elif 'Pages:' in line :

                    num_pages = int(line[7:])

                elif 'Fee:' in line:

                    lines = line.split(' ')
                    fee = lines[1]
                    job.add_currency(lines[2])

                elif 'Journal' in line:

                    if 'URL:' in line:

                        links.append(line[13:])

                    else:

                        job.add_journal(line[9:])

                elif 'REVIEW' in line and 'PLEASE' not in line:

                    links.append(mail_text[index + 1].decode("utf-8"))

                elif 'ACCEPT' in line:

                    links.append(mail_text[index + 1].decode("utf-8"))

                elif 'DECLINE' in line:

                    links.append(mail_text[index + 1].decode("utf-8"))

                elif 'RETURN' in line:

                    links.append(mail_text[index + 1].decode("utf-8"))

                elif 'Due Date:' in line:

                    ind = line.find(' -')
                    job.add_due_date(parse(line[10:ind]))
                    job.add_timezone(line[ind+3:])

                elif 'References:' in line:

                    if 'YES' in line:
                        do_refs = True

                elif 'Figures:' in line:

                    if 'YES' in line:
                        do_figs = True

                elif 'Tables:' in line:

                    if 'YES' in line:
                        do_tabs = True

            # Add to message if necessary and then finally add it to structure
            else:

                if '***' in line and 'Message' not in line:
                    message_running = False
                    job.add_message(message)

                elif '***' not in line:
                    message = message + line

        # Check if jobs is completed/downloaded (placeholders for now)
        is_completed = False
        is_downloaded = False

        # Add the last few things
        job.add_numbers(num_pages, fee)
        job.add_links(links)
        job.add_flags(do_refs, do_figs, do_tabs, is_completed, is_downloaded)

        return job

# Job class
class Job:

    def __init__(self, name, mail_date):

        self.name = name
        self.stage = ""
        self.message = "\n"
        self.doReferences = False
        self.doFigures = False
        self.doTables = False
        self.pages = 0
        self.dueDate = ""
        self.assignDate = mail_date
        self.timeZone = ""
        self.fee = 0
        self.currency = ""
        self.journal = ""
        self.journalLink = ""
        self.reviewLink = ""
        self.acceptLink = ""
        self.declineLink = ""
        self.returnLink = ""
        self.isCompleted = False
        self.isDownloaded = False

    def __str__(self):

        text = 'Job name: ' + self.name + '\nJob stage: ' + self.stage + '\nMessage: ' + self.message + '\nReferences: '

        if self.doReferences:
            text2 = 'Yes\n'
        else:
            text2 = 'No\n'

        text = text + text2 + 'Figures: '

        if self.doFigures:
            text2 = 'Yes\n'
        else:
            text2 = 'No\n'

        text = text + text2 + 'Tables: '

        if self.doTables:
            text2 = 'Yes\n'
        else:
            text2 = 'No\n'

        text = text + text2 + 'Due date: ' + str(self.dueDate) + '\nTime zone: ' + self.timeZone

        text = text + '\nPages: ' + str(self.pages) + '\nFee: ' + str(self.fee) + ' ' + self.currency

        text = text + '\nJournal: ' + self.journal + '\nJournal link: ' + self.journalLink + '\nReview link: '

        text = text + self.reviewLink + '\nAccept link: ' + self.acceptLink + '\nDecline link: ' + self.declineLink

        text = text + '\nReturn link: ' + self.returnLink + '\nAssignment date: ' + self.assignDate.strftime('%B %Y')

        text = text + '\nCompleted: '

        if self.isCompleted:
            text2 = 'Yes\n'
        else:
            text2 = 'No\n'

        text = text + text2 + 'Downloaded: '

        if self.isDownloaded:
            text2 = 'Yes\n'
        else:
            text2 = 'No\n'

        text = text + text2

        return text

    # Set parameters
    def add_stage(self, stage):
        self.stage = stage

    def add_message(self, message):
        self.message = message

    def add_flags(self, do_refs, do_figs, do_tabs, is_completed, is_downloaded):
        self.doReferences = do_refs
        self.doFigures = do_figs
        self.doTables = do_tabs
        self.isCompleted = is_completed
        self.isDownoaded = is_downloaded

    def add_due_date(self, due_date):
        self.dueDate = due_date

    def add_assign_date(self, assign_date):
        self.assignDate = assign_date

    def add_timezone(self, timezone):
        self.timeZone = timezone

    def add_numbers(self, pages, fee):
        self.pages = pages
        self.fee = fee

    def add_currency(self, currency):

        if currency == 'Yen':
            curr_abbrev = 'JPY'
        else: curr_abbrev = currency
        self.currency = curr_abbrev

    def add_journal(self, journal):
        self.journal = journal

    def add_links(self, links):
        self.journalLink = links[0]
        self.reviewLink = links[1]
        self.acceptLink = links[2]
        self.declineLink = links[3]
        self.returnLink = links[4]

    # Get parameters
    def get_fee(self, rates):

        # Convert fee for each rate
        try:
            if self.currency == 'JPY':
                fee = float(self.fee)*rates[0]
            elif self.currency == 'RMB':
                fee = float(self.fee)*rates[1]
            else:
                fee = float(self.fee)*rates[2]
        except ValueError:
            fee = 0
        
        return fee


main()
