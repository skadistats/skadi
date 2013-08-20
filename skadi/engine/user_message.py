import sys
from skadi.protoc import usermessages_pb2 as pb_um
from skadi.protoc import dota_usermessages_pb2 as pb_dota_um

DOTA_UM_ID_BASE = 64

BY_ID = {
    1: 'AchievementEvent',          2: 'CloseCaption',
    3: 'CloseCaptionDirect',        4: 'CurrentTimescale',
    5: 'DesiredTimescale',          6: 'Fade',
    7: 'GameTitle',                 8: 'Geiger',
    9: 'HintText',                 10: 'HudMsg',
   11: 'HudText',                  12: 'KeyHintText',
   13: 'MessageText',              14: 'RequestState',
   15: 'ResetHUD',                 16: 'Rumble',
   17: 'SayText',                  18: 'SayText2',
   19: 'SayTextChannel',           20: 'Shake',
   21: 'ShakeDir',                 22: 'StatsCrawlMsg',
   23: 'StatsSkipState',           24: 'TextMsg',
   25: 'Tilt',                     26: 'Train',
   27: 'VGUIMenu',                 28: 'VoiceMask',
   29: 'VoiceSubtitle',            30: 'SendAudio',
   63: 'MAX_BASE',                 64: 'AddUnitToSelection',
   65: 'AIDebugLine',              66: 'ChatEvent',
   67: 'CombatHeroPositions',      68: 'CombatLogData',
   70: 'CombatLogShowDeath',       71: 'CreateLinearProjectile',
   72: 'DestroyLinearProjectile',  73: 'DodgeTrackingProjectiles',
   74: 'GlobalLightColor',         75: 'GlobalLightDirection',
   76: 'InvalidCommand',           77: 'LocationPing',
   78: 'MapLine',                  79: 'MiniKillCamInfo',
   80: 'MinimapDebugPoint',        81: 'MinimapEvent',
   82: 'NevermoreRequiem',         83: 'OverheadEvent',
   84: 'SetNextAutobuyItem',       85: 'SharedCooldown',
   86: 'SpectatorPlayerClick',     87: 'TutorialTipInfo',
   88: 'UnitEvent',                89: 'ParticleManager',
   90: 'BotChat',                  91: 'HudError',
   92: 'ItemPurchased',            93: 'Ping',
   94: 'ItemFound',                95: 'CharacterSpeakConcept',
   96: 'SwapVerify',               97: 'WorldLine',
   98: 'TournamentDrop',           99: 'ItemAlert',
  100: 'HalloweenDrops',          101: 'ChatWheel',
  102: 'ReceivedXmasGift',        103: 'UpdateSharedContent',
  104: 'TutorialRequestExp',      105: 'TutorialPingMinimap',
  106: 'GamerulesStateChanged',   107: 'ShowSurvey',
  108: 'TutorialFade',            109: 'AddQuestLogEntry',
  110: 'SendStatPopup',           111: 'TutorialFinish'
}

def parse(pbmsg):
  _id = pbmsg.msg_type

  if _id == 106: # wtf one-off?
    ns = pb_dota_um
    cls = 'CDOTA_UM_GamerulesStateChanged'
  else:
    ns = pb_um if _id < DOTA_UM_ID_BASE else pb_dota_um
    infix = 'DOTA' if ns is pb_dota_um else ''
    cls = 'C{0}UserMsg_{1}'.format(infix, BY_ID[_id])

  try:
    _pbmsg = getattr(ns, cls)()
    _pbmsg.ParseFromString(pbmsg.msg_data)
  except AttributeError:
    err = '! protobuf {0}: open an issue at github.com/onethirtyfive/skadi'
    print err.format(cls)
  else:
    try:
      result = getattr(sys.modules[__name__], 'parse_{0}'.format(cls))(_pbmsg)
    except AttributeError:
      result = None
      err = '! unparsed UM {0}: open an issue at github.com/onethirtyfive/skadi'
      print err.format(cls)

    return result

def parse_CUserMsg_SayText2(pbmsg):
  pass

def parse_CUserMsg_TextMsg(pbmsg):
  pass

def parse_CUserMsg_SendAudio(pbmsg):
  pass

def parse_CDOTAUserMsg_ChatEvent(pbmsg):
  pass

def parse_CDOTAUserMsg_UnitEvent(pbmsg):
  pass

def parse_CDOTAUserMsg_ParticleManager(pbmsg):
  pass

def parse_CDOTAUserMsg_SpectatorPlayerClick(pbmsg):
  pass

def parse_CDOTAUserMsg_OverheadEvent(pbmsg):
  pass

def parse_CDOTAUserMsg_LocationPing(pbmsg):
  pass

def parse_CDOTAUserMsg_CreateLinearProjectile(pbmsg):
  pass

def parse_CDOTAUserMsg_DestroyLinearProjectile(pbmsg):
  pass

def parse_CDOTAUserMsg_HudError(pbmsg):
  pass

def parse_CDOTAUserMsg_MinimapEvent(pbmsg):
  pass

def parse_CDOTAUserMsg_DodgeTrackingProjectiles(pbmsg):
  pass

def parse_CDOTAUserMsg_MapLine(pbmsg):
  pass

def parse_CDOTAUserMsg_NevermoreRequiem(pbmsg):
  pass

# This is a one-off, with a weird message class name.
# It may be legacy, appearing only in older replays.
def parse_CDOTA_UM_GamerulesStateChanged(pbmsg):
  pass
