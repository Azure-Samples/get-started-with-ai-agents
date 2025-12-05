PLAYER_MAX = 4		# 最大プレイヤー数（四人打ち麻雀）
ONE_TILE_MAX = 4	# 各牌の最大枚数

WALL_TILES_PER_SEAT = 34  # 各プレイヤーの山の枚数（上段+下段）  
DEAD_WALL_SIZE = 14 # 王牌の枚数（ドラ表示牌＋裏ドラ表示牌＋槓材）

MELD_TYPE_PON = 'ポン'
MELD_TYPE_CHI = 'チー' 
MELD_TYPE_KAN = 'カン'

SUITS = {'萬', '筒', '索'} # 数牌
SUIT_ORDER =  {'萬': 0, '筒': 1, '索': 2}  # 萬→筒→索

SUSI_TILES = {'東','南','西','北'} # 四喜牌
SANGEN_TILES = {'白','発','中'}    # 三元牌
CHINRO_TILES = {'1萬', '9萬', '1筒', '9筒', '1索', '9索'} # 清老頭牌

HORNORS = SUSI_TILES | SANGEN_TILES # 字牌
HORNOR_ORDER = {'東':0,'南':1,'西':2,'北':3,'白':4,'発':5,'中':6} # 東→南→西→北→白→発→中

SEATS = {'東','南','西','北'} # プレイヤーの風
SEAT_ORDER = {'東':0,'南':1,'西':2,'北':3} # 東→南→西→北

