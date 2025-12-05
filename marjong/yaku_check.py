
# yaku_check.py 

import define
import player as player_module
from collections import Counter
from yakuman_check import check_yakuman

# --- helper utilities -------------------------------------------------
def _all_player_tiles(player):
    """
    すべての牌リストを返すヘルパー。

    - プレイヤーの手牌 (`player.hand`) を含む。
    - 自摸（`player.tsumo_tile`）があれば追加する。
    - 鳴き（`player.melds`）があれば、その中の牌も展開して追加する。

    この関数は役判定で手全体を集計する際に利用します。
    """
    tiles = []
    # 単純に player.hand のコピーを扱う（元を破壊しないため）
    tiles.extend(getattr(player, 'hand', []).copy())
    # ツモ牌があれば含める
    if getattr(player, 'tsumo_tile', None):
        tiles.append(player.tsumo_tile)
    # 鳴きは dict 型（{'meld':[...]}) や単純なリストの両方を想定して展開する
    for meld in getattr(player, 'melds', []):
        if isinstance(meld, dict):
            tiles.extend(meld.get('meld', []))
        else:
            tiles.extend(meld)
    return tiles

def _concealed_tiles(player):
    """
    門前（鳴きのない部分）の牌を返すヘルパー。

    通常は `player.hand` と `player.tsumo_tile`（あれば）を結合した一覧を返す。
    ピンフや一盃口など「門前限定」判定に使うための補助関数です。
    """
    tiles = getattr(player, 'hand', []).copy()
    if getattr(player, 'tsumo_tile', None):
        tiles.append(player.tsumo_tile)
    return tiles

def _is_numeric_tile(tile):
    """数牌かどうかを判定する（例: '5m', '2p'）。

    戻り値: True=数牌, False=字牌や不正な形式
    """
    return isinstance(tile, str) and len(tile) == 2 and tile[0].isdigit() and tile[1] in define.SUIT_ORDER

def _tile_suit_num(tile):
    """
    数牌を (数字, 種別) のタプルに変換するヘルパー。

    例: '5m' -> (5, 'm')
    非数牌の場合は (None, None) を返す。
    """
    if not _is_numeric_tile(tile):
        return None, None
    return int(tile[0]), tile[1]

def _tiles_counts(player):
    """プレイヤーの全牌の出現回数カウンタを返すヘルパー。"""
    return Counter(_all_player_tiles(player))


def is_riichi(player_obj):  
    """立直 (リーチ) 判定"""  
    # リーチが成立する条件: 門前でテンパイしリーチ宣言している  
    return len(player_obj.melds) == 0 and player_obj.tsumo_tile is None  
  
def is_tsumo(player):  
    """門前清自摸和 (ツモ) 判定"""  
    # ツモが成立する条件: 門前で自摸和了している  
    return len(player.melds) == 0 and player.tsumo_tile is not None  
  
def is_pinfu(player):
    """平和 (ピンフ) 判定"""
    # ピンフが成立する条件: 門前で両面待ち、副露なし、雀頭が役牌でない
    if len(player.melds) > 0:
        return False
    # 簡易判定: 門前で字牌を含まないこと、雀頭が役牌でないこと
    tiles = _all_player_tiles(player)
    # 字牌が含まれる場合は簡易的にピンフ除外
    if any(tile in define.HORNORS for tile in tiles):
        return False
    # 雀頭が役牌でないことを確認する（厳密な雀頭検出は複雑なので簡易実装）
    # ここではとりあえず門前で字牌がなければ True とする（要改善）
    return True
  
def is_tanyao(player):
    """断么九 (タンヤオ) 判定"""
    # タンヤオの条件: 2～8の数牌のみで構成され、副露していてもよい
    all_tiles = _all_player_tiles(player)
    for t in all_tiles:
        if _is_numeric_tile(t):
            num, _ = _tile_suit_num(t)
            if num < 2 or num > 8:
                return False
        else:
            # 字牌が混ざっていたらタンヤオではない
            return False
    return True

def is_iipeikou(player):
    """一盃口 (簡易判定): 門前かつ同一順子が2組ある場合を検出する簡易実装"""
    if len(player.melds) > 0:
        return False
    tiles = _concealed_tiles(player)
    # 集計: 各種別ごとに数牌のカウンタを作り、順子の出現数を数える
    for suit in define.SUIT_ORDER:
        nums = [int(t[0]) for t in tiles if _is_numeric_tile(t) and t[1] == suit]
        if not nums:
            continue
        cnt = Counter(nums)
        seq_total = 0
        for n in range(1, 8):
            seq_count = min(cnt.get(n, 0), cnt.get(n+1, 0), cnt.get(n+2, 0))
            seq_total += seq_count
        if seq_total >= 2:
            return True
    return False
  
def is_yakuhai(player):
    """役牌判定"""
    # 役牌の条件: 三元牌または場風牌・自風牌の刻子/槓子がある
    winds_and_dragons = list(define.SANGEN_TILES) + [player.wind]
    for meld in player.melds:
        if meld[0] in winds_and_dragons and len(meld) >= 3:
            return True
    return False
YAKU_FAN = {  
    '七対子':2,  
    '清一色':6, '混一色':3,  
    '役牌(east)':1, '役牌(south)':1, '役牌(west)':1, '役牌(north)':1,  
    '役牌(white)':1, '役牌(green)':1, '役牌(red)':1,  
}  

# 役牌
def yakuhai_list(player):
    """鳴き込みを含む手牌から役牌の列表示を返す"""
    hand = player.hand.copy()
    if player.tsumo_tile:
        hand.append(player.tsumo_tile)
    for meld in player.melds:
        hand.extend(meld.get('meld', []))
    counts = Counter(hand)
    # define.HORNORS は日本語の字牌セットを持つ
    return [h for h in define.HORNORS if counts.get(h, 0) >= 3]

# 七対子
def is_chiitoitsu(player):
    hand = player.hand.copy()
    if player.tsumo_tile:
        hand.append(player.tsumo_tile)
    for meld in player.melds:
        hand.extend(meld.get('meld', []))
    if len(hand) != 14:
        return False
    counts = Counter(hand)
    return sorted(counts.values()) == [2] * 7

# 混一色
def is_honitsu(player):
    """混一色: 数牌は同一種別＋字牌を含める"""
    suits = define.SUIT_ORDER.keys()
    hand = player.hand.copy()
    if player.tsumo_tile:
        hand.append(player.tsumo_tile)
    for meld in player.melds:
        hand.extend(meld.get('meld', []))
    suit_tiles = [tile for tile in hand if len(tile) == 2 and tile[1] in define.SUIT_ORDER]
    if not suit_tiles:
        return False
    suit = suit_tiles[0][1]
    return all((len(tile) == 2 and tile[1] == suit) or (tile in define.HORNORS) for tile in hand)

# 清一色
def is_chinitsu(player):
    """清一色: 数牌のみで同一種別のみで構成される"""
    hand = player.hand.copy()
    if player.tsumo_tile:
        hand.append(player.tsumo_tile)
    for meld in player.melds:
        hand.extend(meld.get('meld', []))
    suit_tiles = [tile for tile in hand if len(tile) == 2 and tile[1] in define.SUIT_ORDER]
    if not suit_tiles:
        return False
    suit = suit_tiles[0][1]
    return all(len(tile) == 2 and tile[1] == suit for tile in suit_tiles)

# 天和
def is_tenhou(is_parent, is_first_draw, is_tsumo):  
    # 親が配牌直後（第一自摸前）に和了（≒配牌即和了）  
    # is_parent: 親ならTrue  
    # is_first_draw: 第1ツモ前ならTrue  
    # is_tsumo: ツモ和了時True  
    return is_parent and is_first_draw and is_tsumo 

# 地和
def is_chiihou(is_parent, is_first_draw, is_tsumo):  
    # 子で第1自摸直後にツモ和了したら地和  
    # is_parent: 親ならFalse  
    # is_first_draw: 第1ツモ直後ならTrue  
    # is_tsumo: ツモ和了時True  
    return (not is_parent) and is_first_draw and is_tsumo 
# 人和
def is_renhou(is_parent, is_first_draw, is_ron):  
    # 子が第1自摸前にロン和了したら人和  
    # is_parent: 親ならFalse  
    # is_first_draw: 第1ツモ前ならTrue  
    # is_ron: ロン和了時True  
    return (not is_parent) and is_first_draw and is_ron  

# 一巡目あがり役満チェック
def check_yakuman_first_turn(is_parent, is_first_draw, is_tsumo, is_ron):
    yakuman_list = []  
    if is_tenhou(is_parent, is_first_draw, is_tsumo):  
        yakuman_list.append('天和')  
    if is_chiihou(is_parent, is_first_draw, is_tsumo):  
        yakuman_list.append('地和')  
    if is_renhou(is_parent, is_first_draw, is_ron):  
        yakuman_list.append('人和')  
    return yakuman_list

# 通常役チェック
def check_yaku(player):
    result = []
    fan = 0
    if is_chiitoitsu(player):
        result.append('七対子')
        fan += 2
    if is_chinitsu(player):
        result.append('清一色')
        fan += 6
    if is_honitsu(player):
        result.append('混一色')
        fan += 3
    # ...他の通常役...
    yakuhai = yakuhai_list(player)
    for honor in yakuhai:
        result.append(f'役牌({honor})')
        fan += 1
    if not result:
        result.append('役なし')
    return result, fan

# 全役チェック
def check_all_yaku(player_obj, is_parent=False, is_first_draw=False, is_tsumo=False, is_ron=False):
    """player_obj を受け取り、役満優先で全役を返す
    戻り値: (役リスト, 飜数または役満換算ファン)
    """
    yakuman_list = check_yakuman(player_obj)
    fan = 0
    if yakuman_list:
        # 一巡目役満（天和/地和/人和）を追加でチェック
        yakuman_list.extend(check_yakuman_first_turn(is_parent, is_first_draw, is_tsumo, is_ron))
        fan = 13 * len(yakuman_list)
        return yakuman_list, fan
    else:
        yaku_list, fan = check_yaku(player_obj)  # 通常役
        if fan > 0:
            yakuman_list = check_yakuman_first_turn(is_parent, is_first_draw, is_tsumo, is_ron)
        if not yakuman_list:
            if fan >= 13:
                yakuman_list.append('数え役満')
        if yakuman_list:
            fan = 13 * len(yakuman_list)
            return yakuman_list, fan
        return yaku_list, fan