import pandas as pd
import game.boost as boost

class Player:

    def __init__(self, player_stats_dict=None, actor_data=None):
        self.name = None
        self.online_id = None
        self.team = None  # using team class. set later.
        self.is_orange = None
        self.score = None
        self.goals = None
        self.assists = None
        self.saves = None
        self.shots = None

        self.frame_data = {}

        self.camera_settings = {}
        self.loadout = []

        self.data = None
        self.boosts = None
        self.demos = None

    def __repr__(self):
        if self.team:
            return '%s: %s on %s' % (self.__class__.__name__, self.name, self.team)
        else:
            return '%s: %s' % (self.__class__.__name__, self.name)

    def create_from_actor_data(self, actor_data, teams):
        self.name = actor_data['name']
        self.online_id = actor_data["Engine.PlayerReplicationInfo:UniqueId"]["SteamID64"]
        self.score = actor_data["TAGame.PRI_TA:MatchScore"]
        team_actor_id = actor_data["Engine.PlayerReplicationInfo:Team"]["ActorId"]
        if team_actor_id == -1:
            # if they leave at the end
            team_actor_id = actor_data['team']["ActorId"]
        for team in teams:
            if team.actor_id == team_actor_id:
                self.is_orange = team.is_orange
        assert self.is_orange is not None, 'Cannot find team for player: %s' % self.name
        self.score = actor_data.get("TAGame.PRI_TA:MatchScore", None)
        self.goals = actor_data.get("TAGame.PRI_TA:MatchGoals", None)
        self.assists = actor_data.get("TAGame.PRI_TA:MatchAssists", None)
        self.saves = actor_data.get("TAGame.PRI_TA:MatchSaves", None)
        self.shots = actor_data.get("TAGame.PRI_TA:MatchShots", None)
        self.parse_actor_data(actor_data)
        return self

    def parse_player_stats(self, player_stats):
        self.name = player_stats["Name"]
        self.online_id = player_stats["OnlineID"]
        self.is_orange = bool(player_stats["Team"])
        self.score = player_stats["Score"]
        self.goals = player_stats["Goals"]
        self.assists = player_stats["Assists"]
        self.saves = player_stats["Saves"]
        self.shots = player_stats["Shots"]
        return self

    def get_camera_settings(self, camera_data):
        self.camera_settings['field_of_view'] = camera_data.get('FieldOfView', None)
        self.camera_settings['height'] = camera_data.get('Height', None)
        self.camera_settings['pitch'] = camera_data.get('Pitch', None)
        self.camera_settings['distance'] = camera_data.get('Distance', None)
        self.camera_settings['stiffness'] = camera_data.get('Stiffness', None)
        self.camera_settings['swivel_speed'] = camera_data.get('SwivelSpeed', None)
        self.camera_settings['transition_speed'] = camera_data.get('TransitionSpeed', None)

    def parse_actor_data(self, actor_data):
        self.get_loadout(actor_data)

        self.title = actor_data.get('TAGame.PRI_TA:Title', None)
        self.total_xp = actor_data.get('TAGame.PRI_TA:TotalXP', None)
        self.steering_sensitivity = actor_data.get('TAGame.PRI_TA:SteeringSensitivity', None)
        return self

    def get_loadout(self, actor_data):
        loadout_data = actor_data["TAGame.PRI_TA:ClientLoadouts"]
        for loadout_name, _loadout in loadout_data.items():
            self.loadout.append({
                'version': _loadout.get('Version', None),
                'car': _loadout.get('BodyProductId', None),
                'skin': _loadout.get('SkinProductId', None),
                'wheels': _loadout.get('WheelProductId', None),
                'boost': _loadout.get('BoostProductId', None),
                'antenna': _loadout.get('AntennaProductId', None),
                'topper': _loadout.get('HatProductId', None),
                'engine_audio': _loadout.get('EngineAudioProductId', None),
                'trail': _loadout.get('TrailProductId', None),
                'goal_explosion': _loadout.get('GoalExplosionProductId', None),
                'banner': _loadout.get('BannerProductId', None)
            })
            # TODO: Support painted stuff (look in ClientLoadoutsOnline)

    def parse_data(self, _dict):
        """
        ['ping', 'pos_x', 'pos_y', 'pos_z', 'rot_x', 'rot_y', 'rot_z', 'vel_x',
        'vel_y', 'vel_z', 'ang_vel_x', 'ang_vel_y', 'ang_vel_z', 'throttle',
        'steer', 'handbrake', 'ball_cam', 'dodge_active', 'double_jump_active',
        'jump_active', 'boost', 'boost_active']

        {'ang_vel_x': dtype('float64'),
         'ang_vel_y': dtype('float64'),
         'ang_vel_z': dtype('float64'),
         'ball_cam': dtype('O'),
         'boost': dtype('float64'),
         'boost_active': dtype('O'),
         'dodge_active': dtype('O'),
         'double_jump_active': dtype('O'),
         'handbrake': dtype('O'),
         'jump_active': dtype('O'),
         'ping': dtype('int64'),
         'pos_x': dtype('float64'),
         'pos_y': dtype('float64'),
         'pos_z': dtype('float64'),
         'rot_x': dtype('float64'),
         'rot_y': dtype('float64'),
         'rot_z': dtype('float64'),
         'steer': dtype('float64'),
         'throttle': dtype('float64'),
         'vel_x': dtype('float64'),
         'vel_y': dtype('float64'),
         'vel_z': dtype('float64')}

        :param _dict:
        :return:
        """
        self.data = pd.DataFrame.from_dict(_dict, orient='index')
        self.get_boost()
        pass

    def get_boost(self):
        collection = {}
        usage = {}
        last_boost_amount = 99999
        for frame_number, data_row in self.data.iterrows():
            boost_amt = data_row.loc['boost']
            if boost_amt > last_boost_amount:
                position = data_row.loc['pos_x':'pos_y']
                boost_type = boost.get_boost_type_from_position(position)
                # print("%i  \t%i\t%i\t%i" % (boost_type, boost_amt - last_boost_amount, boost_amt, last_boost_amount))
                collection[frame_number] = boost_type

            elif boost_amt < last_boost_amount:
                usage[frame_number] = last_boost_amount - boost_amt

            last_boost_amount = boost_amt

        self.boosts = pd.DataFrame.from_dict({
            'collection': collection,
            'usage': usage
        }, orient='columns')

        pass