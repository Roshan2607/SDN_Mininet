from pox.core import core
from pox.lib.util import dpidToStr
import pox.openflow.libopenflow_01 as of

log = core.getLogger()

ROUTES = {
    1: {  # s1
        '10.0.0.1': 1,
        '10.0.0.2': 2,
        '10.0.0.3': 2,
    },
    2: {  # s2
        '10.0.0.1': 1,
        '10.0.0.2': 2,
        '10.0.0.3': 2,
    },
    3: {  # s3
        '10.0.0.1': 3,
        '10.0.0.2': 1,
        '10.0.0.3': 2,
    },
}

def install_flow(connection, dst_ip, out_port):
    msg = of.ofp_flow_mod()
    msg.match.dl_type = 0x0800
    msg.match.nw_dst = dst_ip
    msg.actions.append(of.ofp_action_output(port=out_port))
    connection.send(msg)
    log.info(f"IP flow installed on s{connection.dpid} → dst={dst_ip} out_port={out_port}")

def install_arp_flood(connection):
    msg = of.ofp_flow_mod()
    msg.match.dl_type = 0x0806
    msg.actions.append(of.ofp_action_output(port=of.OFPP_FLOOD))
    connection.send(msg)
    log.info(f"ARP flood installed on s{connection.dpid}")

def on_packet_in(event):
    log.info(f"PacketIn on s{event.dpid} port={event.port} — flow rules handling this")

def launch():
    core.openflow.addListenerByName("ConnectionUp", on_connection_up)
    core.openflow.addListenerByName("PacketIn", on_packet_in)
    log.info("Static Router started")

def on_connection_up(event):
    dpid = event.dpid
    log.info(f"Switch connected: s{dpid}")
    install_arp_flood(event.connection)
    if dpid in ROUTES:
        for dst_ip, out_port in ROUTES[dpid].items():
            install_flow(event.connection, dst_ip, out_port)

def launch():
    core.openflow.addListenerByName("ConnectionUp", on_connection_up)
    log.info("Static Router started")