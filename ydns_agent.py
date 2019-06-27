"""
description: agent client to config ydns 
function: YDNS 
class: YDNS
method: handle_cmd/divide_dict/subtract_dict... 
"""
import sys
import time
import getopt
import json
import nshead
from zonedump import ZoneDump
import mcpack
import socket
import traceback
import os 
import ConfigParser 

# Define command id, should be consistent with server side
YDNS_CMD_NOT_EXIST = 0
YDNS_CMD_LIST_SVC = 1
YDNS_CMD_SHOW_VERSION = 2
YDNS_CMD_FORCE_SYNC_ZONE = 6
YDNS_CMD_START_TRACTION = 7
YDNS_CMD_STOP_TRACTION = 8
YDNS_CMD_STAT_QUERY_WORKER = 9
YDNS_CMD_STAT_QUERY_IP = 10
YDNS_CMD_STAT_CLEAR_IP = 11
YDNS_CMD_STAT_CLEAR_WORKER = 12
YDNS_CMD_RELOAD_FILTER = 13
YDNS_CMD_ADD_ZONE = 14
YDNS_CMD_DEL_ZONE = 15
YDNS_CMD_START_FILTER = 16
YDNS_CMD_STOP_FILTER = 17
YDNS_CMD_START_RRL = 18
YDNS_CMD_STOP_RRL = 19
YDNS_CMD_START_ZONE_LIMIT = 20
YDNS_CMD_STOP_ZONE_LIMIT = 21
YDNS_CMD_LIST_ZONE_LIMIT = 22
YDNS_CMD_SET_ZONE_LIMIT = 23
YDNS_CMD_SET_LOG_LEVEL = 24
YDNS_CMD_STAT_SYS =  25
YDNS_CMD_DUMP_ZONES = 26
YDNS_CMD_SYNC_ZONES = 27
YDNS_CMD_DUMP_PKTS = 28
YDNS_CMD_UPDATE_MASTERS = 29

YDNS_CMD_RET_SUCCESS = 0
YDNS_CMD_RET_ID_NOTEXIST = 10
YDNS_CMD_RET_VERSION_MISMATCH = 20
YDNS_CMD_RET_ILLEGAL_PARAMS = 30
YDNS_CMD_RET_INTERNAL_ERROR = 40
YDNS_CMD_RET_NO_SUCH_SERVICE = 50
YDNS_CMD_RET_CLIENT_NOT_ALLOW = 60
YDNS_CMD_RET_FILTER_ALREADY_STARTED = 70
YDNS_CMD_RET_FILTER_ALREADY_STOP = 80

fw = open("./saveydns.logs", mode='w')
string = ""

def subtract_dict(obj1, obj2):
    """
    docstring: subtrack dic
    """
    _total = {}
    for _key in obj1.keys():
        _total[_key] = obj1[_key] - obj2[_key]

    return _total


def divide_dict(obj, divisor):
    """
    docstring: divide dic
    """
    _total = {}
    if divisor == 0:
        return _total
    for _key in obj.keys():
        _total[_key] = obj[_key] / divisor

    return _total


class YDNS(object):
    """
    description: YDNS class 
    """
    def __init__(self, ip, port, verbose_mode, local_cmd, local_opt, timeout):
        self.ip = ip
        self.port = port
        self.is_connected = False
        self.verbose_mode = verbose_mode
        self.local_cmd = local_cmd
        self.local_opt = local_opt
        self.timeout = timeout

    def strerror(self, errno):
        """
        description:strerror
        """
        err_map = {
                YDNS_CMD_RET_SUCCESS: "Success",
                YDNS_CMD_RET_ID_NOTEXIST: "No handler for such command",
                YDNS_CMD_RET_VERSION_MISMATCH: "Agent Version mismatch with server",
                YDNS_CMD_RET_ILLEGAL_PARAMS: "Illegal paramters",
                YDNS_CMD_RET_INTERNAL_ERROR: "Internal error",
                YDNS_CMD_RET_NO_SUCH_SERVICE: "Can not find service",
                YDNS_CMD_RET_CLIENT_NOT_ALLOW: "Client is not allowed",
                YDNS_CMD_RET_FILTER_ALREADY_STARTED: "filter have been started",
                YDNS_CMD_RET_FILTER_ALREADY_STOP: "filter is not running"
        }
        ret = {"code": errno, "msg":err_map[errno]}

        return json.dumps(ret)

    def connect(self):
        """
        description: connect to client 
        """
        try:
            self.sock = socket.create_connection((self.ip, self.port), self.timeout)
            self.is_connected = True
        except:
            print traceback.format_exc()
            sys.exit(2)

    def handle_stat_query_cmd(self, cmd_id, second):
        """
        description: handle stat query cmd 
        """
        old_stat = None
        while True:
            self.send(cmd_id, {})
            (res_nshead, res_body) = self.recv()
            self.close()

            if res_nshead.reserved != YDNS_CMD_RET_SUCCESS:
                print self.strerror(res_nshead.reserved)
                time.sleep(float(second))
                continue

            if old_stat is not None:
                #print(chr(27) + "[2J")
                import os
                os.system('cls' if os.name == 'nt' else 'clear')
                print "\n%s Packets or Bytes per Second:" % \
                       time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(time.time()))
                print res_body
                keys = old_stat.keys()
                keys.sort()
                for key in keys:
                    global string
                    string += str(subtract_dict(res_body[key], old_stat[key]))

            global fw
            print string
            fw.write(string)
            fw.flush()
            string=""
            
            old_stat = res_body
            time.sleep(float(second))
            fw.truncate()
            fw.seek(0,0)

    def handle_sync_zones_cmd(self):
        """
        description: handle cmd sync-zones
        """
        # get zonelist from db
        inst = ZoneDump()
        zones_db = inst.dump()

        #  get zonelist from server
        keys = {}
        self.send(YDNS_CMD_LIST_SVC, keys)
        (res_nshead, res_body) = self.recv()
        self.close()
        if not res_nshead or res_nshead.reserved != YDNS_CMD_RET_SUCCESS:
            print self.strerror(res_nshead.reserved)
            return
        zones_server = res_body['services'][0]['zone']

        zones_section_num = res_body['services'][0]['zonelist_section_num']
        if zones_section_num > 1:
            for i in range(zones_section_num-1):
                self.send(YDNS_CMD_LIST_SVC, keys)
                (res_nshead, res_body) = self.recv()
                self.close()
                if not res_nshead or res_nshead.reserved != YDNS_CMD_RET_SUCCESS:
                    print self.strerror(res_nshead.reserved)
                    return
                zones_server.extend(res_body['services'][0]['zone'])

        # calculate which zones need to be added and which need to be deleted
        to_add = list(set(zones_db).difference(set(zones_server)))
        to_delete = list(set(zones_server).difference(set(zones_db)))
        print "to_add: "
        print to_add
        print "to_delete:"
        print to_delete

        keys['instance'] = res_body['services'][0]['name']
        # add zones
        for  z in to_add:
            keys['zone'] = z
            self.send(YDNS_CMD_ADD_ZONE, keys)
            (res_nshead, res_body) = self.recv()
            self.close()
            if not res_nshead or res_nshead.reserved != YDNS_CMD_RET_SUCCESS:
                print self.strerror(res_nshead.reserved)
                return
            print "add %s success" % z
        # delete zones
        for  z in to_delete:
            keys['zone'] = z
            self.send(YDNS_CMD_DEL_ZONE, keys)
            (res_nshead, res_body) = self.recv()
            self.close()
            if not res_nshead or res_nshead.reserved != YDNS_CMD_RET_SUCCESS:
                print self.strerror(res_nshead.reserved)
                return
            print "delete %s success" % z
 
        return

    def handle_cmd(self, cmd_id, keys):
        """
        description: handle cmd by cmd id 
        """
        if (cmd_id == YDNS_CMD_STAT_QUERY_IP or cmd_id == YDNS_CMD_STAT_QUERY_WORKER):
            second = 60
            if self.local_opt is not None:
                second = self.local_opt
            self.handle_stat_query_cmd(cmd_id, second)
            return

        if cmd_id == YDNS_CMD_SYNC_ZONES:
            self.handle_sync_zones_cmd()
            return

        self.send(cmd_id, keys)
        (res_nshead, res_body) = self.recv()
        self.close()

        if self.verbose_mode == True:
            print "Response:"
            print res_nshead
            print res_body
        if not res_body:
            print self.strerror(res_nshead.reserved)
        else:
            print json.dumps(res_body, indent=4)
        return

    def recv(self):
        """
        description: recv cmd 
        """
        try:
            res_nshead = nshead.NsHead.from_str(self.sock.recv(36))

            recved = 0
            body = ''
            res_body = ''
            start_time = time.time()
            while recved < res_nshead.body_len:
                temp = self.sock.recv(1024)
                recved += len(temp)
                body = body + temp

                # Receive timeout, so break the loop
                if time.time()-start_time > self.timeout:
                    raise Exception('Recv timeout')

            if body != '':
                res_body = mcpack.loads(body)

            return (res_nshead, res_body)
        except:
            print traceback.format_exc()
            sys.exit(2)

    def send(self, cmd_id, keys):
        """
        description: send cmd 
        """
        try:
            if self.is_connected == False:
                self.connect()
            head = nshead.NsHead()
            head.id = cmd_id
            # TODO parse keys
            body = keys
            mcpack_body = mcpack.dumps(body)
            head.body_len = len(mcpack_body)

            if self.verbose_mode == True:
                print "Send:"
                print head
                print body

            request = head.pack() + mcpack_body
            self.sock.send(request)
        except:
            print traceback.format_exc()
            sys.exit(2)

    def close(self):
        """
        description: close connection 
        """
        try:
            self.is_connected = False
            self.sock.shutdown(socket.SHUT_WR)
            self.sock.close()
            self.sock = None
        except:
            print(traceback, format_exc())
            sys.exit(2)


def usage():
    """
        description: usage 
    """
    print 'Usage: python ydns_agent.py [-hVL] [TARGET] [COMMAND] [OPTIONS]...'
    print '-h|--help              show usage'
    print '-V|--verbose           verbose mode'
    print '-L|--loglevel LEVEL    set loglevel,can be notice|info|warning|error'
    print '-s|--server  SERVER    server ip or hostname'
    print '-r|--rrl               rrl options'
    print '-Z|--zonelimit         zonelimit options'
    print '-f|--filter            filter options'
    print '-i|--instance  NAME    service(instance) name or VIP'
    print '-v|--view      NAME    view name'
    print '-z|--zone      NAME    zone name'
    print '-d|--domain    NAME    domain name'
    print '-t|--type      NAME    domain type, can be a|aaaa|ns|cname|ns|ptr|mx'
    print '-m|--master    IP      ip:port/'
    print '-c|--cmd         command name'
    print '-o|--opt         command options'
    print '\nServer commands:'
    print '    version      show server version'
    print '    stats        show system stats'
    print '        -o base|memory|cycle|pkts '
    print '    list         list all services configurations'
    print '    query-ip     show network stats by ip'
    print '    query-worker show network stats by worker'
    print '    clear-ip     clear ip stats'
    print '    clear-worker clear worker stats'
    print '    dump-zones   dump all zones to local files'
    print '    sync-zones   sync zonelist with db'
    print '    dump-pkts    copy packets from receiver to vnic'
    print '        -o     start|stop     control switch based on demand'
    print '\nService commands:'
    print '    start        start bgp traction'
    print '    stop         stop bgp traction'
    print '\nZone commands:'
    print '    addzone      add new zone'
    print '    delzone      del zone'
    print '    force-sync   force sync zone'
    print '    set-zonelimit      set zonelimit'
    print '        -o true|false    control start/stop zone-limit per domain'
    print '        -o PERIOD/BYTES/QUERIES   0/0/0 for default'
    print '\nRRL commands:'
    print '    start        start rrl'
    print '    stop         stop rrl'
    print '\nFilter commands:'
    print '    start        start filter'
    print '    stop         stop filter'
    print '    reload       reload ip white list'
    print '\nZonelimit commands:'
    print '    start        start zonelimit'
    print '    stop         stop zonelimit'
    print '    list         list zonelimit'
    print '# list services configurations'
    print 'python ydns_agent.py -s xx.xx.xx.xx -c list\n'
    print '# show system stats'
    print 'python ydns_agent.py -s xx.xx.xx.xx -c stats -o base|memory|cycle|pkts\n'
    print '# show network stats'
    print 'python ydns_agent.py -s xx.xx.xx.xx -c query-ip|query-worker [-o 5]\n'
    print '# start or stop bgp traction'
    print 'python ydns_agent.py -s xx.xx.xx.xx -i SERVICE -c start|stop\n'
    print '# sync zonelist with db'
    print 'python ydns_agent.py -s xx.xx.xx.xx -c sync-zones\n'
    print '# modify filter'
    print 'python ydns_agent.py -s xx.xx.xx.xx -f -c start|stop|reload\n'
    print '# modify zone'
    print 'python ydns_agent.py -s xx.xx.xx.xx -i SERVICE -z ZONE -c addzone|delzone|force-sync\n'
    print '# modify zonelimit for specified zone'
    print 'python ydns_agent.py -s xx.xx.xx.xx -i SERVICE -z ZONE \
-c set-zonelimit -o 5/10000/100\n'
    print '# modify masters\' ip and port'
    print 'python ydns_agent.py -s xx.xx.xx.xx -i SERVICE -m ip:port/ip:port/ -c update\n'
    print '# modify global zonelimit'
    print 'python ydns_agent.py -s xx.xx.xx.xx -Z -c start|stop|list\n'
    print '# dump pkts from receiver to vnic'
    print 'python ydns_agent.py -s xx.xx.xx.xx -c dump-pkts -o start|stop\n'

def main(argv):
    """
        description: main 
    """
    if(len(argv) < 2):
        usage()
        sys.exit(0)

    shortargs = 'hVL:s:rZfi:v:z:d:t:c:o:m:'
    longargs = ['help', 'verbose', 'loglevel=', 'server=', 'rrl',\
                 'zonelimit', 'filter', 'instance=', 'view=', 'zone=', 'domain=',\
                 'type=', 'cmd=', 'opt=', 'masters=']
    try:
        opts, args = getopt.getopt(sys.argv[1:], shortargs, longargs)
    except getopt.GetoptError as err:
        print str(err)
        sys.exit(0)

    server = None
    cmd_id = YDNS_CMD_NOT_EXIST
    enter_rrl = False
    enter_filter = False
    enter_zonelimit = False
    keys = {}

    # use only in local, will not send to server
    local_cmd = None
    local_opt = None

    verbose_mode = False
    for o, a in opts:
        if o in ('-h', '--help'):
            usage()
            sys.exit(0)
        elif o in ('-V', '--verbose'):
            verbose_mode = True
        elif o in ('-L', '--loglevel') and a != '':
            cmd_id = YDNS_CMD_SET_LOG_LEVEL
            keys['loglevel'] = a
        elif o in ('-s', '--server') and a != '':
            server = a
        elif o in ('-r', '--rrl'):
            enter_rrl = True
        elif o in ('-Z', '--zonelimit'):
            enter_zonelimit = True
        elif o in ('-f', '--filter'):
            enter_filter = True
        elif o in ('-i', '--instance') and a != '':
            keys['instance'] = a
        elif o in ('-v', '--view') and a != '':
            keys['view'] = a
        elif o in ('-z', '--zone') and a != '':
            keys['zone'] = a
        elif o in ('-d', '--domain') and a != '':
            keys['domain'] = a
        elif o in ('-t', '--type') and a != '':
            keys['type'] = a
        elif o in ('-m', '--masters') and a != '':
            keys['masters'] = a
        elif o in ('-c', '--cmd') and a != '':
            local_cmd = a
        elif o in ('-o', '--opt') and a != '':
            local_opt = a
        else:
            print o, a, 'unhandled option'
            sys.exit(1)

    #print keys
    #if keys.has_key('instance') and keys.has_key('view') and keys.has_key('zone') and local_cmd:
        #elif keys.has_key('instance') and keys.has_key('zone') and local_cmd:
    if not local_cmd and cmd_id == YDNS_CMD_NOT_EXIST:
        print 'illegal input'
        sys.exit(1)

    if 'instance' in keys and 'zone' in keys:
        if local_cmd == 'addzone':
            cmd_id = YDNS_CMD_ADD_ZONE
        elif local_cmd == 'delzone':
            cmd_id = YDNS_CMD_DEL_ZONE
        elif local_cmd == 'force-sync':
            cmd_id = YDNS_CMD_FORCE_SYNC_ZONE
        elif local_cmd == 'set-zonelimit':
            cmd_id = YDNS_CMD_SET_ZONE_LIMIT
            keys['elements'] = local_opt
    elif 'instance' in keys and 'masters' in keys:
        if local_cmd == 'update':
            cmd_id = YDNS_CMD_UPDATE_MASTERS
    #elif keys.has_key('instance') and local_cmd:
    elif 'instance' in keys:
        if local_cmd == 'start':
            cmd_id = YDNS_CMD_START_TRACTION
        elif local_cmd == 'stop':
            cmd_id = YDNS_CMD_STOP_TRACTION
    elif enter_zonelimit:
        if local_cmd == 'start':
            cmd_id = YDNS_CMD_START_ZONE_LIMIT
        elif local_cmd == 'stop':
            cmd_id = YDNS_CMD_STOP_ZONE_LIMIT
        elif local_cmd == 'list':
            cmd_id = YDNS_CMD_LIST_ZONE_LIMIT
    elif enter_filter:
        if local_cmd == 'start':
            cmd_id = YDNS_CMD_START_FILTER
        elif local_cmd == 'stop':
            cmd_id = YDNS_CMD_STOP_FILTER
        elif local_cmd == 'reload':
            cmd_id = YDNS_CMD_RELOAD_FILTER
    elif enter_rrl:
        if local_cmd == 'start':
            cmd_id = YDNS_CMD_START_RRL
        elif local_cmd == 'stop':
            cmd_id = YDNS_CMD_STOP_RRL
    else:
        if local_cmd == 'version':
            cmd_id = YDNS_CMD_SHOW_VERSION
        elif local_cmd == 'query-ip':
            cmd_id = YDNS_CMD_STAT_QUERY_IP
        elif local_cmd == 'query-worker':
            cmd_id = YDNS_CMD_STAT_QUERY_WORKER
        elif local_cmd == 'clear-worker':
            cmd_id = YDNS_CMD_STAT_CLEAR_WORKER
        elif local_cmd == 'clear-ip':
            cmd_id = YDNS_CMD_STAT_CLEAR_IP
        elif local_cmd == 'stats':
            keys['stat'] = local_opt
            cmd_id = YDNS_CMD_STAT_SYS
        elif local_cmd == 'list':
            cmd_id = YDNS_CMD_LIST_SVC
        elif local_cmd == 'dump-zones':
            cmd_id = YDNS_CMD_DUMP_ZONES
        elif local_cmd == 'sync-zones':
            cmd_id = YDNS_CMD_SYNC_ZONES
        elif local_cmd == 'dump-pkts':
            keys['copy'] = local_opt
            cmd_id = YDNS_CMD_DUMP_PKTS

    if cmd_id == YDNS_CMD_NOT_EXIST:
        print 'illegal input'
        sys.exit(1)
    if not server:
        print 'should specify dns server [-s xx.xx.xx.xx ]'
        sys.exit(1)
    ydns = YDNS(server, 10057, verbose_mode, local_cmd, local_opt, 30)
    ydns.handle_cmd(cmd_id, keys)

if __name__ == '__main__':
    main(sys.argv)
