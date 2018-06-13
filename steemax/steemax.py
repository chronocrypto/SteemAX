#!/usr/bin/python3

import re
import sys
from cmd import Cmd
from steemax import axe
from steemax import axdb
from steemax import axverify
from steemax import axtrans
from screenlogger.screenlogger import Msg

msg = Msg()
db = axdb.AXdb("steemax", "SteemAX_pass23", "steemax")
xverify = axverify.AXverify()

# Entry point
def run(args=None):
    db.first_time_setup()
    prompt = MyPrompt()
    prompt.prompt = '[steemax]# '
    prompt.cmdloop('\n   ** Welcome to SteemAX ** \n')



class Enter():



    def account_name(self, flag, mode):
        ''' Prompt user for their Steemit account name. 
        'flag' indicates entering the account name 
        for an invitee or inviter
        '''
        if flag:
            question = 'Your account name @'
        else:
            question = 'Their account name @'
        while True:
            acct = input(question)
            if (not re.match(r'^[a-z0-9\-]+$', acct)
                            or len(acct) == 0 
                            or len(acct) > 32):
                msg.message('The account name you entered is '
                            + 'blank or contains invalid characters.')
            else:
                if xverify.get_vote_value(acct, 100, 0, mode):
                    break
        return acct



    def memo_id(self, acct):
        ''' Prompt user for the unique Memo ID that 
        was generated during the creation of an invite
        '''
        while True:
            memoid = input('Memo ID: ')
            if (not re.match( r'^[0-9]+$', memoid) 
                            or len(memoid) == 0 
                            or len(memoid) > 32):
                msg.message('The Memo ID you entered is '
                            + 'blank or contains invalid characters.')
            else:
                if db.verify_memoid(acct, memoid):
                    break
                else:
                    return False
        return memoid



    def percentage(self, acct):
        ''' Prompt user for the percentage of their 
        upvote they wish to exchange. 
        This is always a percentage of the inviter's 
        (Account1) upvote, not the invitee (Account2)
        '''
        while True:
            per = input(
                '''Percentage of {}'s upvote (1 to 100):'''.format(acct))
            if (not re.match( r'^[0-9]+$', per) 
                            or len(per) == 0 
                            or len(per) > 3 
                            or int(per) < 1 
                            or int(per) > 100):
                msg.message('Please only enter a number '
                            + 'between 1 and 100.')
            else:
                break
        return per



    def ratio(self, acct1, acct2, per, flag):
        ''' Prompt user for the ratio between 
        accounts for the exchanges. This ratios 
        is expressed as a two digit decimal number
        to two places in proportion to 1, i.e. 
        XX.xx to 1. e.g. 0.01 to 1, 10.10 to 1, 
        1.25 to 1, etc.
        This is always so that X is inviter's 
        (Account1) upvote, to 1 which is the 
        invitee's (Account2) upvote
        '''
        while True:
            ratio = input('Enter ratio '
                    + 'as X ({}) to 1 ({}). X is: '.format(acct1, acct2))
            if (not re.match( r'^[0-9\.]+$', ratio) 
                            or len(ratio) == 0 
                            or len(ratio) > 5 
                            or float(ratio) < 0.01 
                            or float(ratio) > 99):
                msg.message('Please enter a one or two '
                            + 'digit number to represent a ratio in '
                            + 'the format x to 1 where x is your '
                            + 'input. Enter a decimal to two places '
                            + 'to represent a ratio less than one. '
                            + 'e.g. 0.05 to 1')
            else:
                if xverify.eligible_votes(acct1, acct2, 
                                        per, ratio, "", flag):
                    break
        return ratio



    def duration(self):
        ''' Promt user to enter the 
        duration of the auto exchange 
        in the number of days
        '''
        while True:
            dur = input('Duration of exchange in days: ')
            if (not re.match( r'[0-9]', dur) 
                            or len(dur) == 0 
                            or len(dur) > 3):
                msg.message('Please only enter a number '
                            + 'up to three digits.')
            else:
                break
        return dur



    def key(self, acct):
        ''' Prompt user for their private 
        posting key as found in their 
        steemit.com wallet or for their
        SteemConnect Refresh Token as 
        given by the auth_url login
        '''
        msg.message(xverify.steem.connect.auth_url())
        while True:
            
            key = input('Your Private Posting Key or'
                        + ' SteemConnect Refresh Token: ')
            if len(key) < 16:
                msg.error_message('The private posting key you '
                                    + 'entered is too small.')
            elif xverify.steem.verify_key(acct, key):
                self.privatekey = xverify.steem.privatekey
                self.refreshtoken = xverify.steem.refreshtoken
                self.accesstoken = xverify.steem.accesstoken
                break




class MyPrompt(Cmd):
    ''' Command line interface for SteemAX
    '''



    def do_run(self, args):
        axe.run_exchanges("")



    def do_process(self, args):
        xtrans = axtrans.AXtrans()
        xtrans.fetch_history()



    def do_invite(self, args):
        ''' Start an auto-upvote exchange 
        between two Steemit accounts 
        '''
        enter = Enter()

        acct1 = enter.account_name(1, "verbose")
        acct2 = enter.account_name(0, "verbose")
        enter.key(acct1)
        per = enter.percentage(acct1)
        ratio = enter.ratio(acct1, acct2, per, 1)
        dur = enter.duration()
        memoid = db.add_invite(acct1, acct2, enter.privatekey, 
                                enter.refreshtoken, enter.accesstoken, 
                                per, ratio, dur)
        if memoid:
            msg.message('An invite has been created. To '
                        + 'authorize this exchange and to send '
                        + 'the invite please send any amount of '
                        + 'SBD to @steem-ax along with the following '
                        + 'memo message. Your SBD will be forwarded '
                        + 'to the invitee:\n\n   '
                        + '{}:start'.format(memoid))
        else:
            msg.message("An invite could not be created.")



    def do_accept(self, args):
        ''' Accept an invite to an exchange
        '''
        acct = Enter().account_name(1, "")
        memoid = Enter().memo_id(acct)
        if int(db.check_status(memoid)) < 0:
            msg.error_message('''The inviter has not yet 
                                authorized the exchange.''')
            return False
        key = Enter().key(acct)
        if db.accept_invite(acct, memoid, key):
            msg.message('The exchange invite has been accepted. '
                        + 'To authorize this change send any amount '
                        + 'of SBD to @steem-ax along with the following '
                        + 'memo message. The SBD you send will be forwarded '
                        + 'to the other party: \n\n  '
                        + '{}:accept'.format(memoid))
        else:
            msg.error_message("Could not accept the invite.")



    def do_barter(self, args):
        ''' Barter on the 
        percentage, ratio and 
        duration of an exchange
        '''
        acct = Enter().account_name(1, "")
        memoid = Enter().memo_id(acct)
        if not db.verify_memoid(acct, memoid):
            return False
        msg.message('{} is the inviter and {} is the invitee.'.format(
                    db.inviter, db.invitee))
        per = Enter().percentage(acct1)
        ratio = Enter().ratio(acct1, acct2, per, 1)
        dur = Enter().duration()
        msg.message('To initiate this barter send '
                    + 'any amount SBD to @steem-ax with '
                    + 'the following in the memo:\n\n  '
                    + '{}:barter:{}:{}:{}'.format(
                    memoid, per, ratio, dur))



    def do_cancel(self, args):
        ''' Cancel an invite to an exchange
        '''
        acct = Enter().account_name(1, "")
        memoid = Enter().memo_id(acct)
        if not db.verify_memoid(acct, memoid):
            return
        if db.cancel(acct, memoid):
            msg.message("The exchange has been canceled")
            


    def do_eligible(self, args):
        ''' Find out if a certain 
        percentage and ratio between 
        two accounts will create an 
        eligible exchange
        '''
        acct1 = Enter().account_name(1, "verbose")    
        acct2 = Enter().account_name(0, "verbose")
        per = Enter().percentage(acct1)
        ratio = Enter().ratio(acct1, acct2, per, 0)



    def do_account(self, args):
        ''' Find and verify a Steemit 
        account and see if it has 
        started an exchange
        '''
        acct = Enter().account_name(1, "verbose")



    def do_pool(self, args):
        ''' Display current Steemit Reward Balance, 
        Recent Claims and price of STEEM
        '''
        xverify.print_steemit_balances()



    def do_quit(self, args):
        """Quits the program."""
        print ("Quitting.")
        raise SystemExit



    def do_exit(self, args):
        """Quits the program."""
        print ("Quitting.")
        raise SystemExit



# Run as main

if __name__ == "__main__":
    if sys.version_info[0] < 3:
        raise Exception("Python 3 or a more recent version is required.")
    run()

# EOF

