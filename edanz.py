import sys
import imaplib
import getpass
import email
import pickle
from time import mktime
from datetime import *
from dateutil.parser import *


def main():

    jobsLoaded = False
    exitProg = False

    # Print options
    print('Editing database manager v. 0.0.1')

    while not exitProg:
    
        print('\nChoose your option:')
        print('1: scan for new messages')
        print('2: save job list')
        print('3: load job list')
        print('4: print current job list')
        print('5: clear current job list')
        print('6: quit')

        choice = input('What do you want to do? ')
        if choice == '1':

            # Clear current list
            jobList = []

            # Input email
            address = input('Enter email: ')
            
            # Scan for messages
            msgList = getMessages(address)

            if msgList != None:

                # Now parse those emails and build the job list
                for msg in msgList:
                    jobList.append(parse_mail(msg))

                jobsLoaded = True
                
        elif choice == '2':

            if not jobsLoaded:
                print('ERROR: No job list loaded.')
            else:
                # Save job list
                saveJobList(jobList,'jobdata.pkl')
                print('Job list saved.')
            
        elif choice == '3':

            # Load job list
            jobList = loadJobList('jobdata.pkl')
            jobsLoaded = True
            print('Job list loaded.')

        elif choice == '4':

            if not jobsLoaded:
                print('ERROR: No job list loaded.')
            else:
                # Print job list
                for job in jobList:
                    print('\n')
                    print(job)
                    
        elif choice == '5':

            jobList = []
            jobsLoaded = False
            print('Job list cleared.')

        elif choice == '6':

            print('Bye!')
            exitProg = True
            
        else:
            print('ERROR: Input not recognised. Try again.')

    # We're done here!
    sys.exit()
   
    
# Given a list of Job objects and a filename, pickle the list to a binary file.
def saveJobList(jobs,fname):

    f = open(fname, 'wb')

    pickle.dump(jobs, f, -1)
          
    f.close()


# Given a filename, unpickle a list of Job objects from a binary file and return it.
def loadJobList(fname):

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
        searchDate = date.today()-timedelta(days=10)
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
                    fee = int(lines[1])
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

        # Add the last few things
        job.add_numbers(num_pages, fee)
        job.add_links(links)
        job.add_flags(do_refs, do_figs, do_tabs)

        return job

# Job class
class Job:

    def __init__(self, name, mail_date):

        self.name = name
        self.stage = ""
        self.isRev = False
        self.isPBP = False
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
        self.completed = False

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

        if self.completed:
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

    def add_flags(self, do_refs, do_figs, do_tabs):
        self.doReferences = do_refs
        self.doFigures = do_figs
        self.doTables = do_tabs

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
        self.currency = currency

    def add_journal(self, journal):
        self.journal = journal

    def add_links(self, links):
        self.journalLink = links[0]
        self.reviewLink = links[1]
        self.acceptLink = links[2]
        self.declineLink = links[3]
        self.returnLink = links[4]



main()
