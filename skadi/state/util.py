import collections as c


def enum(**enums):
  _enum = type('Enum', (), enums)
  _enum.tuples = enums
  return _enum


PVS = enum(Preserve = 0, Enter = 1 << 0, Leave = 1 << 1, Delete = 0x03)


GameEvent = c.namedtuple('GameEvent', 'id, name, keys')


Entity = c.namedtuple('Entity', 'ind, serial, cls, state')


String = c.namedtuple('String', 'ind, name, value')


Snapshot = c.namedtuple('Snapshot', 'tick, entities, string_tables, \
    modifiers, game_events, user_messages')


Prop = c.namedtuple('Prop',
    'src, name, type, flags, pri, len, bits, dt, low, high, array_prop')


Type = enum(
    Int       = 0, Float  = 1, Vector = 2,
    VectorXY  = 3, String = 4, Array  = 5,
    DataTable = 6, Int64  = 7)


Flag = enum(
    Unsigned              = 1 <<  0, Coord                   = 1 <<  1,
    NoScale               = 1 <<  2, RoundDown               = 1 <<  3,
    RoundUp               = 1 <<  4, Normal                  = 1 <<  5,
    Exclude               = 1 <<  6, XYZE                    = 1 <<  7,
    InsideArray           = 1 <<  8, ProxyAlways             = 1 <<  9,
    VectorElem            = 1 << 10, Collapsible             = 1 << 11,
    CoordMP               = 1 << 12, CoordMPLowPrecision     = 1 << 13,
    CoordMPIntegral       = 1 << 14, CellCoord               = 1 << 15,
    CellCoordLowPrecision = 1 << 16, CellCoordIntegral       = 1 << 17,
    ChangesOften          = 1 << 18, EncodedAgainstTickcount = 1 << 19)


UserMessageByKind = {
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
  114: 'SendFinalGold',           115: 'CustomMsg',
  116: 'CoachHUDPing',            117: 'ClientLoadGridNav'
}


def humanize_type(_type):
    for k, v in Type.tuples.items():
        if _type == v:
            return k.lower()


def humanize_flags(flags):
    named_flags = []

    for k, v in Flag.tuples.items():
        if flags & v:
            named_flags.append(k.lower())

    return named_flags


def humanize_state(recv_table, state):
    humanized = dict()

    for i, v in state.items():
        humanized['{}.{}'.format(recv_table.dt, recv_table[i].name)] = v

    return humanized


def parse_game_event(pb, keys):
    attrs = []

    for i, (k_type, k_name) in enumerate(keys):
        key = pb.keys[i]

        if k_type == 1:
            value = key.val_string
        elif k_type == 2:
            value = key.val_float
        elif k_type == 3:
            value = key.val_long
        elif k_type == 4:
            value = key.val_short
        elif k_type == 5:
            value = key.val_byte
        elif k_type == 6:
            value = key.val_bool
        elif k_type == 7:
            value = key.val_uint64

        attrs.append(value)

    return pb.eventid, attrs
