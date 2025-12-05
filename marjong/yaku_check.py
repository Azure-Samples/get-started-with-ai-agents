
# yaku_check.py 

import define
import player as player_module
from collections import Counter  
from yakuman_check import check_yakuman

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
    # 両面待ち・雀頭判定は牌構成に基づく詳細なロジックが必要
    # 以下は簡易例 (実際はもっと詳細な判定が必要)
    return True  # 実際のロジックでは牌構成を分析
  
def is_tanyao(player):
    """断么九 (タンヤオ) 判定"""
    # タンヤオの条件: 2～8の数牌のみで構成され、副露していてもよい
    all_tiles = player.hand + [tile for meld in player.melds for tile in meld]
    return all(int(tile[0]) >= 2 and int(tile[0]) <= 8 for tile in all_tiles if len(tile) == 2 and tile[1] in define.SUIT_ORDER)
  
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
def yakuhai_list(hand):  
    honors = ['east', 'south', 'west', 'north', 'white', 'green', 'red']  
    counts = Counter(hand)  
    return [h for h in honors if counts[h] >= 3]  

# 七対子
def is_chiitoitsu(hand):  
    if len(hand) != 14: return False  
    counts = Counter(hand)  
    return sorted(counts.values()) == [2]*7 

# 混一色
def is_honitsu(hand):  
    suits = ['m', 'p', 's']  
    honors = ['east', 'south', 'west', 'north', 'white', 'green', 'red']  
    suit_tiles = [tile for tile in hand if len(tile) == 2 and tile[1] in suits]  
    if not suit_tiles: return False  
    suit = suit_tiles[0][1]  
    return all((len(tile) == 2 and tile[1] == suit) or (tile in honors) for tile in hand) 

# 清一色
def is_chinitsu(hand):  
    suits = ['m', 'p', 's']  
    suit_tiles = [tile for tile in hand if len(tile) == 2 and tile[1] in suits]  
    if not suit_tiles: return False  
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
def check_yakuman_first_turn(hand, is_parent, is_first_draw, is_tsumo, is_ron):
    yakuman_list = []  
    if is_tenhou(is_parent, is_first_draw, is_tsumo):  
        yakuman_list.append('天和')  
    if is_chiihou(is_parent, is_first_draw, is_tsumo):  
        yakuman_list.append('地和')  
    if is_renhou(is_parent, is_first_draw, is_ron):  
        yakuman_list.append('人和')  
    return yakuman_list

# 通常役チェック
def check_yaku(hand):  
    result = []  
    fan = 0  
    if is_chiitoitsu(hand):  
        result.append('七対子'); fan += 2  
    if is_chinitsu(hand):  
        result.append('清一色'); fan += 6  
    if is_honitsu(hand):  
        result.append('混一色'); fan += 3  
    # ...他の通常役...  
    yakuhai = yakuhai_list(hand)  
    for honor in yakuhai:  
        result.append(f'役牌({honor})'); fan += 1  
    if not result:  
        result.append('役なし')  
    return result, fan

# 全役チェック
def check_all_yaku(hand, is_parent=False, has_drawn_tile=True):  
    yakuman_list = check_yakuman(hand, is_parent, has_drawn_tile) 
    fan = 0
    if yakuman_list:  
        yakuman_list.extend(check_yakuman_first_turn(hand, is_parent, is_first_draw, is_tsumo, is_ron))
        fan = 13 * len(yakuman_list)
        return yakuman_list, fan
    else:  
        yaku_list, fan = check_yaku(hand)  # 通常役
        if fan > 0:
            yakuman_list = check_yakuman_first_turn(hand, is_parent, is_first_draw, is_tsumo, is_ron)
        if not yakuman_list:
            if fan >= 13:
                yakuman_list.append('数え役満') 
        if yakuman_list:
            fan = 13 * len(yakuman_list)
            return yakuman_list, fan
        return yaku_list, fan