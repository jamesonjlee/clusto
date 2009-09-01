
import clusto
from clusto.test import testbase

from clusto.drivers import Driver, PortMixin
from clusto.exceptions import ConnectionException

class TestDev1(Driver, PortMixin):
    _clusto_type = "test1"
    _driver_name = "test1driver"

    _portmeta = {'a' : {'numports':5},
                 'b' : {'numports':1}}

class TestDev2(Driver, PortMixin):

    _clusto_type = "test2"
    _driver_name = "test2driver"

    _portmeta = {'a' : {'numports':4},
                 'z' : {'numports':1}}

class PortLess(Driver):
    _clusto_type = "portless"
    _driver_name = "portless"

class PortTests(testbase.ClustoTestBase):
    """Test the port framework"""

    
    def data(self):
        
        a = TestDev1('t1')
        b = TestDev2('t2')
        c = PortLess('p')

    def testPortTypes(self):
        
        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        
        self.assertEqual(sorted(t1.portTypes), 
                         sorted(['a', 'b']))

        self.assertEqual(sorted(t2.portTypes), 
                         sorted(['a', 'z']))

    def testPortExists(self):
        
        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        self.assertTrue(t1.port_exists('a', 3))
        self.assertTrue(t1.port_exists('a', 0))
        self.assertFalse(t1.port_exists('a', 5))
        self.assertFalse(t1.port_exists('z', 3))

        self.assertTrue(t2.port_exists('z', 0))
        self.assertFalse(t2.port_exists('z', 1))

    def testPortsConnectable(self):
        
        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        self.assertTrue(t1.portsConnectable('a', 1, t2, 3))
        self.assertFalse(t1.portsConnectable('a', 1, t2, 5))
        self.assertFalse(t1.portsConnectable('b', 1, t2, 1))

    def testPortFree(self):
        
        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        self.assertTrue(t1.port_free('a', 2))

        t1.connect_ports('a', 1, t2, 1)

        self.assertFalse(t1.port_free('a', 1))

    def testConnectPorts(self):
        
        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        t1.connect_ports('a', 1, t2, 3)

        
        self.assertEqual(t2, t1.get_connected('a', 1))
        self.assertEqual(t1, t2.get_connected('a', 3))

        self.assertEqual(None, t1.get_connected('b', 0))


        # try to work with ports that don't exist
        self.assertRaises(ConnectionException, t2.get_connected, 'b', 3)
        self.assertRaises(ConnectionException, t2.connect_ports, 'b', 2, t1, 7)
        self.assertRaises(ConnectionException, t2.connect_ports, 'z', 1, t1, 1)


        # try to connect ports that are already connected but in the reverse order
        self.assertRaises(ConnectionException, t2.connect_ports, 'a', 4, t1, 1)

        # try to connect to a device that doesn't have ports
        self.assertRaises(ConnectionException, t1.connect_ports, 'a', 2, p, 1)

    def testDisconnectPort(self):

        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        t1.connect_ports('a', 1, t2, 3)

        self.assertEqual(t2, t1.get_connected('a', 1))
        
        t2.disconnect_port('a', 3)

        self.assertEqual(None, t1.get_connected('a', 1))
        self.assertEqual(None, t2.get_connected('a', 3))

        self.assertTrue(t1.port_free('a', 1))
        self.assertTrue(t2.port_free('a', 3))

        
    def testPortAttrs(self):

        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        t1.set_port_attr('a', 0, 'macaddr', 'foo')
        self.assertEqual('foo', t1.getPortAttrs('a', 0, 'macaddr'))

        self.assertRaises(ConnectionException, 
                          t2.set_port_attr, 'j', 2, 'foo', 'bar')

        self.assertEqual(None, t2.getPortAttrs('z', 0, 'mac'))
        t2.set_port_attr('z', 0, 'mac', 'bar')
        self.assertEqual('bar', t2.getPortAttrs('z', 0, 'mac'))
        t2.delPortAttr('z', 0, 'mac')
        self.assertEqual(None, t2.getPortAttrs('z', 0, 'mac'))
        


    def testPortInfo(self):
        
        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        self.assertEqual(sorted([('a', 0, None, None,),
                                 ('a', 1, None, None,),
                                 ('a', 2, None, None,),
                                 ('a', 3, None, None,),
                                 ('a', 4, None, None,),
                                 ('b', 0, None, None,),]),
                         sorted(t1.portInfoTuples))

        
        t1.connect_ports('a', 2, t2, 1)

        self.assertEqual(sorted([('a', 0, None, None,),
                                 ('a', 1, t1, 2,),
                                 ('a', 2, None, None,),
                                 ('a', 3, None, None,),
                                 ('z', 0, None, None,),]),
                         sorted(t2.portInfoTuples))

        self.assertEqual(t1, t2.portInfo['a'][1]['connection'])
        self.assertEqual(2, t2.portInfo['a'][1]['otherportnum'])

        self.assertEqual(None, t2.portInfo['a'][3]['connection'])
        self.assertEqual(None, t2.portInfo['z'][0]['otherportnum'])

        self.assertEqual(sorted([('a', 0),
                                 ('a', 2),
                                 ('a', 3),
                                 ('z', 0),]),
                         sorted(t2.freePorts))

        self.assertEqual(sorted(['a', 'b']),
                         sorted(t1.portTypes))

        self.assertEqual(sorted(['a', 'z']),
                         sorted(t2.portTypes))


    def testConnectedPorts(self):

        t1, t2, p = map(clusto.get_by_name, ['t1', 't2', 'p'])

        for i in [t1, t2]:
            for t in i.portTypes:
                self.assertEqual([], i.connectedPorts[t])

        t1.connect_ports('a', 1, t2, 3)
        t2.connect_ports('a', 2, t1, 2)
        
        self.assertEqual([1, 2], t1.connectedPorts['a'])
        
