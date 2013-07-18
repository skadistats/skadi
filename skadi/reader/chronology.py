from skadi.domain import chronology
from skadi.generated import demo_pb2 as pb_d
from skadi.generated import netmessages_pb2 as pb_n
from skadi.io import protobuf as io_p

def read(io):
  _chronology = chronology.Chronology()
  iter_d = iter(io)
  pbmsg = next(iter_d, None) # skip the stray CDemoPacket
  pos = io.tell()
  pbmsg = next(iter_d, None)
  while not isinstance(pbmsg, pb_d.CDemoStop):
    if isinstance(pbmsg, pb_d.CDemoFullPacket):
      packet_io = io_p.Packet.wrapping(pbmsg.packet.data)
      for _pbmsg in iter(packet_io):
        if isinstance(_pbmsg, pb_n.CNETMsg_Tick):
          _chronology.note(_pbmsg.tick, pos)
          break
    pos = io.tell()
    pbmsg = next(iter_d, None)
  return _chronology
