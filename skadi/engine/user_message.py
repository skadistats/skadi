import sys

from skadi.protoc import usermessages_pb2 as pb_um
from skadi.protoc import dota_usermessages_pb2 as pb_dota_um


DOTA_UM_ID_BASE = 64

NAME_BY_TYPE = {
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
  110: 'SendStatPopup',           111: 'TutorialFinish',
  112: 'SendRoshanPopup',         113: 'SendGenericToolTip',
  114: 'SendFinalGold'
}

CHAT_MESSAGE_BY_TYPE = {
   -1: 'INVALID',                   0: 'HERO_KILL',
    1: 'HERO_DENY',                 2: 'BARRACKS_KILL',
    3: 'TOWER_KILL',                4: 'TOWER_DENY',
    5: 'FIRSTBLOOD',                6: 'STREAK_KILL',
    7: 'BUYBACK',                   8: 'AEGIS',
    9: 'ROSHAN_KILL',              10: 'COURIER_LOST',
   11: 'COURIER_RESPAWNED',        12: 'GLYPH_USED',
   13: 'ITEM_PURCHASE',            14: 'CONNECT',
   15: 'DISCONNECT',               16: 'DISCONNECT_WAIT_FOR_RECONNECT',
   17: 'DISCONNECT_TIME_REMAINING',18: 'DISCONNECT_TIME_REMAINING_PLURAL',
   19: 'RECONNECT',                20: 'ABANDON',
   21: 'SAFE_TO_LEAVE',            22: 'RUNE_PICKUP',
   23: 'RUNE_BOTTLE',              24: 'INTHEBAG',
   25: 'SECRETSHOP',               26: 'ITEM_AUTOPURCHASED',
   27: 'ITEMS_COMBINED',           28: 'SUPER_CREEPS',
   29: 'CANT_USE_ACTION_ITEM',     30: 'CHARGES_EXHAUSTED',
   31: 'CANTPAUSE',                32: 'NOPAUSESLEFT',
   33: 'CANTPAUSEYET',             34: 'PAUSED',
   35: 'UNPAUSE_COUNTDOWN',        36: 'UNPAUSED',
   37: 'AUTO_UNPAUSED',            38: 'YOUPAUSED',
   39: 'CANTUNPAUSETEAM',          40: 'SAFE_TO_LEAVE_ABANDONER',
   41: 'VOICE_TEXT_BANNED',        42: 'SPECTATORS_WATCHING_THIS_GAME',
   43: 'REPORT_REMINDER',          44: 'ECON_ITEM',
   45: 'TAUNT',                    46: 'RANDOM',
   47: 'RD_TURN',                  48: 'SAFE_TO_LEAVE_ABANDONER_EARLY',
   49: 'DROP_RATE_BONUS',          50: 'NO_BATTLE_POINTS',
   51: 'DENIED_AEGIS',             52: 'INFORMATIONAL',
   53: 'AEGIS_STOLEN',             54: 'ROSHAN_CANDY',
   55: 'ITEM_GIFTED',              56: 'HERO_KILL_WITH_GREEVIL'
}

def parse(pbmsg):
  _type = pbmsg.msg_type

  if _type == 106: # wtf one-off?
    ns = pb_dota_um
    cls = 'CDOTA_UM_GamerulesStateChanged'
  else:
    ns = pb_um if _type < DOTA_UM_ID_BASE else pb_dota_um
    infix = 'DOTA' if ns is pb_dota_um else ''
    cls = 'C{0}UserMsg_{1}'.format(infix, NAME_BY_TYPE[_type])

  try:
    _pbmsg = getattr(ns, cls)()
    _pbmsg.ParseFromString(pbmsg.msg_data)
  except UnicodeDecodeError, e:
    print '! unable to decode protobuf: {}'.format(e)
  except AttributeError, e:
    err = '! protobuf {0}: open an issue at github.com/onethirtyfive/skadi'
    print err.format(cls)

  return _type, _pbmsg
