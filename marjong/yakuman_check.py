# yakuman_check.py 

import define
import player
from collections import Counter  

yakuman_multiplier = {  
    '国士無双': 1,  
    '国士無双十三面待ち': 2,  
    '大三元': 1,  
    '大四喜': 1,  
    '小四喜': 1,  
    '四槓子': 1,  
    '清老頭': 1,  
    '字一色': 1,  
    '緑一色': 1,  
    '四暗刻': 1,  
    '四暗刻単騎待ち': 2,  
    '九蓮宝燈': 1,  
    '純正九蓮宝燈': 2,  
    # 天和等も追加可  
    '天和': 1,  
    '地和': 1,  
    '人和': 1,  
}  

kokushi_set = define.CHINRO_TILES | define.HORNORS
ryuiiso_set = {'2索', '3索', '4索', '6索', '8索', '発'}

# 国士無双
def is_kokushi(player):  
    # 和了時の手牌（13枚+ツモ牌で14枚）  
    hand = player.hand.copy()  
    # 手持ちで13枚揃っている場合は十三面待ち
    if kokushi_set.issubset(set(hand)):
        return False

    if player.add_tile:  
        hand.append(player.add_tile)  
    if len(hand) != 14:  
        return False  
  
    if not kokushi_set.issubset(set(hand)):  
        return False
  
    counts = Counter(hand)  
    # どれかの牌が2枚あること  
    return any(counts[tile] == 2 for tile in kokushi_set)  

# 十三面待ち国士無双
def is_kokushi13(player):  
    hand = player.hand.copy()  
    # 手持ちで13枚揃ってなければ十三面待ちではない
    if not kokushi_set.issubset(set(hand)):
        return False
  
    if player.add_tile:  
        hand.append(player.add_tile)
    if len(hand) != 14:  
        return False  
  
    # 国士無双成立条件  
    if not kokushi_set.issubset(set(hand)):  
        return False

    # 十三面待ち判定：ロンorツモした牌が国士無双構成牌で、ペアがその牌  
    counts = Counter(hand)  
    return player.add_tile in kokushi_set and counts[player.add_tile] == 2 

# 大三元
def is_daisangen(player):
    sangen_tiles = list(define.SANGEN_TILES)

    for meld in player.melds:
        if not meld["type"] == define.MELD_TYPE_CHI:
            for sangen_tile in sangen_tiles:
                if meld["meld"].count(sangen_tile) >= 3:
                    sangen_tiles.remove(sangen_tile)
                    if len(sangen_tile)== 0:
                        return True                        

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        

    counts = Counter(hand)  
    return all(counts[h] == 3 for h in sangen_tiles)

# 大四喜
def is_daisushi(player):
    susi_tiles = list(define.SUSI_TILES)

    for meld in player.melds:
        if not meld["type"] == define.MELD_TYPE_CHI:
            for susi_tile in susi_tiles:
                if meld["meld"].count(susi_tile) >= 3:
                    susi_tiles.remove(susi_tile)
                    if len(susi_tiles)== 0:
                        return True                        

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        

    counts = Counter(hand)  
    return all(counts[h] == 3 for h in susi_tiles)

# 小四喜
def is_shosuushi(player):  
    susi_tiles = list(define.SUSI_TILES)

    for meld in player.melds:
        if not meld["type"] == define.MELD_TYPE_CHI:
            for susi_tile in susi_tiles:
                if meld["meld"].count(susi_tile) >= 3:
                    susi_tiles.remove(susi_tile)
                    if len(susi_tiles)== 0:
                        return False # 四喜牌を全てポン／カンしていたら大四喜                       

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        
    
    counts = Counter(hand)  

    susi_member_num = 0
    susi_head_num = 0
    for susi_tile in susi_tiles:
        if  counts[susi_tile] == 3:
            susi_member_num = susi_member_num + 1

        if  counts[susi_tile] == 2:
            susi_head_num = susi_head_num + 1
            if susi_head_num > 1:
                return False    # 頭が２つあるor七対子は除外

    if susi_head_num == 0:
        return False    # 頭がない場合は大四喜or未成立

    return susi_member_num + susi_head_num == len(susi_tiles)

# 四槓子
def is_suukantsu(player):  
    kan_melds = [meld for meld in player.melds if meld['type'] == define.MELD_TYPE_KAN]
    if len(kan_melds) != 4:
        return False

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        

    counts = Counter(hand)  
    # ツモ牌がペアであること
    return player.add_tile is not None and counts.get(player.add_tile, 0) == 2 

# 清老頭
def is_chinroutou(player):  
    chinro_tiles = list(define.CHINRO_TILES)  

    for meld in player.melds:
        if not meld["type"] == define.MELD_TYPE_CHI:
            for chinro_tile in chinro_tiles:
                if meld["meld"].count(chinro_tile) < 3:
                    return False    # 清老頭不成立

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        
    
    counts = Counter(hand)  

    chinro_member_num = 0
    chinro_head_num = 0
    for chinro_tile in chinro_tiles:
        if counts[chinro_tile] == 3:
            chinro_member_num = chinro_member_num + 1

        if counts[chinro_tile] == 2:
            chinro_head_num = chinro_head_num + 1
            if chinro_head_num > 1:
                return False    # 頭が２つあるor七対子は除外
    
    if chinro_head_num == 0:
        return False    # 頭がない場合は清老頭不成立

    return chinro_member_num * 3 + chinro_head_num * 2 == len(hand)

# 字一色
def is_tsuiso(player):  
    hornor_tiles = list(define.HORNORS)  

    for meld in player.melds:
        if not meld["type"] == define.MELD_TYPE_CHI:
            for hornor_tile in hornor_tiles:
                if meld["meld"].count(hornor_tile) < 3:
                    return False    # 字一色不成立

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        
    
    counts = Counter(hand)  

    hornor_member_num = 0
    hornor_head_num = 0
    for hornor_tile in hornor_tiles:
        if counts[hornor_tile] == 3:
            hornor_member_num = hornor_member_num + 1

        if counts[hornor_tile] == 2:
            hornor_head_num = hornor_head_num + 1
            if hornor_head_num > 1:
                return False    # 頭が２つあるor七対子は除外
    
    if hornor_head_num == 0:
        return False    # 頭がない場合は字一色不成立

    return hornor_member_num * 3 + hornor_head_num * 2 == len(hand)

# 緑一色
def is_ryuiiso(player):  
    """緑一色: 2索、3索、4索、6索、8索、発のみで構成"""
    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        
    
    # 鳴き牌も含める
    for meld in player.melds:
        hand.extend(meld.get("meld", []))
    
    # すべての牌が緑一色に含まれることを確認
    return all(tile in ryuiiso_set for tile in hand)  

# 四暗刻
def is_suuankou(player): 
    ankan_num = 0
    for meld in player.melds:
        if not meld["type"] == define.MELD_TYPE_KAN:
            return False    # ポン・チーがあれば四暗刻不成立
        elif not meld["from_player"] == player.player_id:
            return False    # 他家からのカンがあれば四暗刻不成立
        else:
            ankan_num = ankan_num + 1

    hand = player.hand.copy()  
    if player.add_tile:  
        hand.append(player.add_tile)        
    
    counts = Counter(hand)  
    if sum(1 for v in counts.values() if v == 3) < 4 - ankan_num:  
        return False    # 暗刻が4つに満たない場合は不成立

    return sum(1 for v in counts.values() if v == 2) == 1  # 頭が1つあることを確認

# 四暗刻単騎待ち
def is_suuankou_tanki(player):  
    if not is_suuankou(player):
        return False    # 四暗刻自体が成立していなければ不成立
    # 単騎待ちの場合のみTrueを返す（実装は省略）
    return True


# 九蓮宝燈チェック
def is_churen_check(tiles):
    suits = list(define.SUITS)  
    # 全て同一色の数牌  
    suit_tiles = [tile for tile in tiles if len(tile) == 2 and tile[1] in suits]  
    if not suit_tiles or len(suit_tiles) != 14:  
        return False    # 数牌14枚でなければ不成立
    suit = suit_tiles[0][1]  

    if not all(tile[1] == suit for tile in suit_tiles):  
        return False    # 同一色でなければ不成立
    nums = [int(tile[0]) for tile in suit_tiles]  

    for n in range(1, 10):  
        if nums.count(n) < 1:  
            return False  # 1-9が1枚以上でなければ不成立

    if nums.count(1) < 3 or nums.count(9) < 3:
        return False    # 1か9が3枚以上でなければ不成立

    return True    

# 九蓮宝燈
def is_churen(player):  
    tiles = player.hand.copy()  
    if player.add_tile:  
        tiles.append(player.add_tile)        

    for meld in player.melds:
        if meld["type"] == define.MELD_TYPE_KAN:
            return False    # カンがあれば九蓮宝燈不成立 
        else:
            tiles.extend(meld["meld"])  # 鳴き牌を手牌に追加

    if not is_churen_check(tiles):
        return False    # 九蓮宝燈不成立
        
    counts = Counter(tiles)  
    return counts[player.add_tile] == 1


# 純正九蓮宝燈  
def is_junsei_churen(player):  
    tiles = player.hand.copy()  
    if player.add_tile:  
        tiles.append(player.add_tile)        

    for meld in player.melds:
        if meld["type"] == define.MELD_TYPE_KAN:
            return False    # カンがあれば九蓮宝燈不成立 
        else:
            tiles.extend(meld["meld"])  # 鳴き牌を手牌に追加

    if not is_churen_check(tiles):
        return False    # 九蓮宝燈不成立
        
    counts = Counter(tiles)  
    # ツモ牌が和了牌である場合のみ純正九蓮宝燈
    return player.add_tile is not None and counts.get(player.add_tile, 0) == 2

# 役満チェック
def check_yakuman(player_obj):  
    """
    プレイヤーオブジェクトから役満を判定する
    :param player_obj: Playerオブジェクト
    :return: 役満名のリスト
    """
    yakuman_list = []  
    if is_kokushi13(player_obj):
        yakuman_list.append('国士無双十三面待ち')
    elif is_kokushi(player_obj):  
        yakuman_list.append('国士無双')  
    elif is_tsuiso(player_obj):  
        yakuman_list.append('字一色')  

    if is_daisangen(player_obj):  
        yakuman_list.append('大三元')  

    if is_daisushi(player_obj):  
        yakuman_list.append('大四喜')  
    elif is_shosuushi(player_obj):  
        yakuman_list.append('小四喜')  

    if is_chinroutou(player_obj):  
        yakuman_list.append('清老頭')  

    if is_suukantsu(player_obj):  
        yakuman_list.append('四槓子')  

    if is_ryuiiso(player_obj):  
        yakuman_list.append('緑一色')  

    if is_suuankou_tanki(player_obj):
        yakuman_list.append('四暗刻単騎待ち')
    elif is_suuankou(player_obj):  
        yakuman_list.append('四暗刻')

    if is_junsei_churen(player_obj):
        yakuman_list.append('純正九蓮宝燈')
    elif is_churen(player_obj):  
        yakuman_list.append('九蓮宝燈')

    return yakuman_list

# 役満倍数計算
def calc_yakuman_multipliers(yakuman_list):  
    """  
    yakuman_list: 役満名のリスト  
    戻り値: 各役満の倍率リスト、合計倍率  
    """  
    # 倍率辞書は適宜importや上記定義を参照  
    multipliers = []  
    for yaku in yakuman_list:  
        m = yakuman_multiplier.get(yaku, 1)  # 未登録は1倍として扱う  
        multipliers.append(m)  
    total = sum(multipliers)  
    return multipliers, total