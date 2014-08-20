# This Class is part of the jaide/jgui project.
# It is free software for use in manipulating junos devices. More information can be found at the github page found here:
# 
#  [INSERT GITHUB URL ]

"""
WorkerThread Class 
------------------
Purpose: This class takes command and a queue during construction, runs the command with the doJaide() method,
either in a multiple processing pool for multiple devices, or in one call to doJaide() if we are running against a
single device. Any output is written to the jaide_gui.outputArea and potentially also to an output file, if the user
specified so. It also provides functionality for ending the subprocess before completion.

The class inherits the class threading.Thread, with the purpose of overwriting the run() method of the standard Thread class.
"""

import threading
import Queue
import multiprocessing
import os
import jaide

class WorkerThread(threading.Thread):
    """ WorkerThread class, inheriting threading.Thread. Used to execute the script in a thread. 
    """
    def __init__(self, argsToPass, timeout, command, stdout_queue, ip, username, password, write_to_file):
        """ Purpose: The initialize funtion for the WorkerThread Class. The parameters are all used to pass information down to 
                     doJaide() for executing the script properly. Only the ip and write_to_file parameters are tested against or 
                     used within WorkerThread.

        Parameters: 
            argsToPass      - list - The list of all the arguments that need to be passed through doJaide() for proper script execution.
            timeout         - integer - The timeout value in seconds for the ncclient or paramiko session. The default value set within 
                                        Jaide.py is 300 seconds.
            command         - string - The name of the function within jaide.py that we will be executing to accomplish the goal of the user.
                                       An example of this being deciphered and used is within the class jaide_gui.__init__() method. 
            stdout_queue     - Queue.Queue() - A queue where all output will be put, the writeToQueue() method is used as a callback function for
                                              the doJaide() method, so that any results from doJaide() are writted to the stdout_queue. The 
                                              stdout_queue is actively watched by the jaide_gui.__getoutput() method for printing output to the user.
            ip              - string - The IP string can be one of three things: A single IP address, a comma separated list of IPs, or a filepath 
                                       pointing to a plaintext file of IPs, each one on a separate line. The WorkerThread.run() method handles the 
                                       logic of finding out which of the three we have received, and acting accordingly.
            username        - string - The username for authenticating against the devices listed in the 'ip' parameter.
            password        - string - The password for authenticating against the devices listed in the 'ip' parameter.
            write_to_file   - string - either an empty string (meaning we're not writing to a file), or a filepath pointing to the desired
                                       output file for the script output. jaide_gui.run() will determine if we're writing to a file or not, 
                                       and take the appropriate action. 
        """
        super(WorkerThread, self).__init__()
        self.argsToPass = argsToPass
        self.timeout = timeout
        self.command = command
        self.stdout_queue = stdout_queue
        self.ip = ip
        self.username = username
        self.password = password
        self.write_to_file = write_to_file
        # Set number of threads to 2x number of cores. Usually cpu_count returns twice the physical cores due to hyperthreading.
        self.mp_pool = multiprocessing.Pool(multiprocessing.cpu_count()*2)
        self.wtfQueue = Queue.Queue()

    def writeToQueue(self, results):
        """ Purpose: This function is used for callback from pressing the 'Run Script' button. It will always output to 
                     the stdout_queue, which __writeToOutputArea is watching, and will therefore be showed to the user 
                     within the output area at the bottom of the application. 

                     The if statement will also put the outputs into the queue being watched by the 'run' function, which 
                     will output the results to the output file they specified.

            Parameters: 
                results  -  string  -  the results that will be dropped into the output area, and possibly also the output file, 
                                       if write_to_file is true/checked.
        """
        self.stdout_queue.put(results)
        if self.write_to_file:
            self.wtfQueue.put(results)

    def run(self):
        """ Purpose: This overwrites threading.Thread's run() method. It is called by doing WorkerThread.start(). The overaching goal
                     is to decide if we are running against a single IP address, or against a list of IP's. If we are doing the latter,
                     we need to start a multiprocessing pool, and run the doJaide method for each IP address asynchronously. 

                     The script is executed, either via writeToQueue() directly for a single IP address, or mp_pool.apply_async() 
                     with a callback to writeToQueue() for a list of IP addresses. Once we have executed the script, we check the 
                     write_to_file parameter to see if we need to output to a file.
        """
        iplist = ""
        if len(self.ip.split(',')) > 1:
            # multiple IPs passed in with commas
            iplist = self.ip.split(',')
        elif os.path.isfile(self.ip):
            # file was passed in for IP
            try:
                iplist = open(self.ip, 'rb')
            except IOError as e:
                self.stdout_queue.put("Couldn't open IP list file " + self.ip + " due to the error:\n" + str(e))
        else:
            iplist = []
            iplist.append(self.ip)

        # If we're doing an action against more than one device, we need to run the doJaide function in a multiprocessing pool,
        # to run against all devices at the same time. 
        if iplist != "":
            for IP in iplist:
                IP = IP.strip()
                if IP != "":  # skip blank lines
                    if IP[0] != "#":  # skip comments in an IP list file. 
                        self.mp_pool.apply_async(doJaide, args=(IP, self.username, self.password, self.command, self.timeout, self.argsToPass), callback=self.writeToQueue)
            self.mp_pool.close()
            self.mp_pool.join()

        # If we're writing output to a file, we open the output file and write the Queue here. 
        if self.write_to_file:
            try:
                out_file = open(self.write_to_file, "a+b")
            except IOError as e:
                self.stdout_queue.put("Could not save script output to file. Error:\n" + str(e))
            else:
                while not self.wtfQueue.empty():
                    out_file.write(self.wtfQueue.get())
                self.writeToQueue("\nSuccessfully wrote/appended output to " + self.write_to_file + "\n")


    def join(self, timeout=None):
        """ Purpose: Provide a method for joining the threads to the main-thread, to ensure that the parent thread (jgui) knows when
                     the sub-thread (WorkerThread) has finished, and can continue. 
        """
        super(WorkerThread, self).join(timeout)

    
    def kill_proc(self):
        """ Purpose: Provide a way to kill the subprocess from outside of the thread. 
            Terminating the pool leaves nothing left blocking self.run() so it completes and exits normally.
        """
        self.mp_pool.terminate()


def doJaide(ip, username, password, command, timeout, argsToPass):
    """ Purpose: This function is created outside of the WorkerThread class due to the limitation that a method within the WorkerThread 
                 class could not be 'pickled' for multiprocessing when running against more than one IP address. 
    """
    # an SCP operation is handled serpately, calling the jaide.copy_file function
    if command == jaide.copy_file:
        return jaide.copy_file(
            argsToPass["scp_source"], 
            argsToPass["scp_dest"], 
            ip, 
            username, 
            password, 
            argsToPass["direction"], 
            argsToPass["write"], 
            argsToPass["multi"], 
            argsToPass["callback"]
        )
    # All other functions are handled by do_netconf(), with a standardized argsToPass variable for handling args. 
    else:
        return jaide.do_netconf(ip, username, password, command, argsToPass, "", timeout)
