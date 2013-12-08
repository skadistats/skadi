import importlib as il
import os

__impl__ = 'skadi_ext' if os.environ.get('SKADI_EXT') else 'skadi'
ndx_gnrc = il.import_module(__impl__ + '.index.generic')

from protobuf.impl import demo_pb2 as pb_d


def parse(io_demo):
    """
    Process a specialized 'demo' IO wrapper into a PrologueIndex.

    Don't forget to bootstrap() the IO first, since there are 16 bytes of
    non-protobuf header data at the beginning of a demo file. Your use case
    may vary, so this method does not bootstrap.

    Arguments:
    io_demo -- DemoIO (skadi.io.demo) wrapping a file stream

    """
    entries = []
    iter_io = iter(io_demo)

    peek, message = next(iter_io)
    try:
        while True:
            entries.append((peek, message))
            peek, message = next(iter_io)
    except StopIteration:
        pass

    return EpilogueIndex(entries)


class EpilogueIndex(ndx_gnrc.Index):
    """
    Facilitates constant-time, expressive fetching of 'dem' messages at end of
    match. These messages follow a single CDemoStop (protobuf.impl.demo_pb2)
    message toward the end of the replay.

    FIXME: Make this more functional, ex. 'match_id' property, etc.

    """

    def __init__(self, entries):
        """
        Initialize instance of index.

        Argument:
        entries -- list of (peek, message) to index

        """
        super(EpilogueIndex, self).__init__(entries)

        self.__file_info = None
        self.__dota_dota_game_info = None
        self.__dem_file_info = None

    @property
    def playback_time(self):
        """
        Playback time as per the summary near end of file, in seconds.

        """
        return self._file_info.playback_time

    @property
    def playback_ticks(self):
        """
        Playback tick count as per the summary near end of file.

        """
        return self._file_info.playback_ticks

    @property
    def playback_frames(self):
        """
        Playback frame count as per the summary near end of file.

        The number of frames corresponds to the number of snapshots in the
        demo, which are typically every other tick. Therefore, this number is
        approximately (playback_ticks / 2).

        """
        return self._file_info.playback_frames

    @property
    def match_id(self):
        """
        The unique Match ID assigned to this specific game.

        """
        return self._dota_game_info.match_id

    @property
    def game_mode(self):
        """
        TODO: Research and write enum containing possible values.

        """
        return self._dota_game_info.game_mode

    @property
    def game_winner(self):
        """
        TODO: Research and write enum containing possible values.

        """
        return self._dota_game_info.game_winner

    @property
    def league_id(self):
        """
        TODO: Research and explain.

        """
        return self._dota_game_info.leagueid

    @property
    def radiant_team_id(self):
        """
        TODO: Research and explain.

        """
        return self._dota_game_info.radiant_team_id

    @property
    def radiant_team_tag(self):
        """
        TODO: Research and explain.

        """
        return self._dota_game_info.radiant_team_tag

    @property
    def dire_team_id(self):
        """
        TODO: Research and explain.

        """
        return self._dota_game_info.dire_team_id

    @property
    def dire_team_tag(self):
        """
        TODO: Research and explain.

        """
        return self._dota_game_info.dire_team_tag

    @property
    def end_time(self):
        """
        TODO: Research and explain.

        """
        return self._dota_game_info.end_time

    @property
    def players(self):
        """
        TODO: Research and explain.

        """
        records = []

        for pi in self._dota_game_info.player_info:
            record = {
                'hero_name': pi.hero_name,
                'player_name': pi.player_name,
                'is_fake_client': pi.is_fake_client,
                'steam_id': pi.steamid,
                'game_team': pi.game_team
            }
            records.append(record)

        return records

    @property
    def picks_bans(self):
        """
        TODO: Research and explain.

        """
        records = []

        for hs in self._dota_game_info.picks_bans:
            record = {
                'is_pick': hs.is_pick,
                'team': hs.team,
                'hero_id': hs.hero_id
            }
            records.append(record)

        return records

    @property
    def _dota_game_info(self):
        """
        Dig into the file info for the appropriate struct.

        """
        return self._file_info.game_info.dota

    @property
    def _file_info(self):
        """
        Dig into the file info for the appropriate struct.

        """
        if not self.__file_info:
            peek, message = self._dem_file_info

            pb = pb_d.CDemoFileInfo()
            pb.ParseFromString(message)

            self.__file_info = pb

        return self.__file_info

    @property
    def _dem_file_info(self):
        """
        Returns (peek, message) for 'file info.'

        """
        if not self.__dem_file_info:
            self.__dem_file_info = self.find_kind(pb_d.DEM_FileInfo)

        assert self.__dem_file_info
        return self.__dem_file_info
