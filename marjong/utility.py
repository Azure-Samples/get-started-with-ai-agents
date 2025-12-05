def is_sequence(tiles):  
    """順子判定 (例: 123, 234 など)"""  
    return len(tiles) == 3 and tiles[1] == tiles[0] + 1 and tiles[2] == tiles[0] + 2  

def can_form_meld(tiles):
    """刻子または順子を作れるかチェック"""
    if len(tiles) == 3:
        # 刻子チェック (例: 111, 999 など)
        if tiles[0] == tiles[1] == tiles[2]:
            return True
        # 順子チェック (例: 123, 456 など)
        if is_sequence(sorted(tiles)):  # 順序をソートして判定  
            return True

    return False  

def is_complete_hand(player):  
    """
    プレイヤーの手牌と鳴いた面子が揃っているかをチェックする関数。  
    面子（刻子・順子）と雀頭が揃っているかを判定する。  
    """
    # 手牌 + 鳴いた面子を結合  
    total_tiles = player.hand + [tile for meld in player.melds for tile in meld]  
  
    # 牌のカウントを取得  
    tile_count = Counter(total_tiles)    # 面子を揃えるためのチェック  
    melds = []  # 刻子・順子を格納  
    pair_found = False  # 雀頭が見つかったかどうか  
  
    for tile, count in tile_count.items():  
        if count >= 3:  # 刻子を作れる場合  
            melds.append([tile] * 3)  
            tile_count[tile] -= 3  
        elif count == 2 and not pair_found:  # 雀頭を作れる場合  
            pair_found = True  
            tile_count[tile] -= 2  
  
    # 順子の判定 (数牌のみ)  
    for tile in sorted(tile_count.keys()):  
        while tile_count[tile] > 0 and tile_count[tile + 1] > 0 and tile_count[tile + 2] > 0:  
            melds.append([tile, tile + 1, tile + 2])  
            tile_count[tile] -= 1  
            tile_count[tile + 1] -= 1  
            tile_count[tile + 2] -= 1  
  
    # 判定: 面子 + 雀頭が揃っているか  
    return pair_found and len(melds) + len(player.melds) == 4 
  
def is_valid_sequence(tiles):  
    """順子が正しいか確認する（例: [1, 2, 3]）"""  
    return len(tiles) == 3 and tiles[1] == tiles[0] + 1 and tiles[2] == tiles[0] + 2  
  
def find_winning_patterns(hand):  
    """  
    手牌からすべての和了パターンと和了牌を探索。  
    hand: 手牌 (リスト)  
    """  
    def backtrack(remaining_tiles, melds, pairs):  
        # ベースケース: すべての牌が使われたら解決  
        if not remaining_tiles:  
            if len(melds) == 4 and len(pairs) == 1:  
                results.append((melds[:], pairs[:]))  
            return  
  
        # 残りの牌をカウント  
        tile_counts = Counter(remaining_tiles)  
  
        # 雀頭を選択  
        for tile in tile_counts:  
            if tile_counts[tile] >= 2:  
                remaining_tiles_copy = remaining_tiles[:]  
                remaining_tiles_copy.remove(tile)  
                remaining_tiles_copy.remove(tile)  
                pairs.append([tile, tile])  
                backtrack(remaining_tiles_copy, melds, pairs)  
                pairs.pop()  
          
        # 刻子を選択  
        for tile in tile_counts:  
            if tile_counts[tile] >= 3:  
                remaining_tiles_copy = remaining_tiles[:]  
                remaining_tiles_copy.remove(tile)  
                remaining_tiles_copy.remove(tile)  
                remaining_tiles_copy.remove(tile)  
                melds.append([tile, tile, tile])  
                backtrack(remaining_tiles_copy, melds, pairs)  
                melds.pop()  
          
        # 順子を選択  
        for tile in tile_counts:  
            if tile + 1 in tile_counts and tile + 2 in tile_counts:  
                remaining_tiles_copy = remaining_tiles[:]  
                remaining_tiles_copy.remove(tile)  
                remaining_tiles_copy.remove(tile + 1)  
                remaining_tiles_copy.remove(tile + 2)  
                melds.append([tile, tile + 1, tile + 2])  
                backtrack(remaining_tiles_copy, melds, pairs)  
                melds.pop()  
  
    def is_valid_combination(hand, melds, pairs, winning_tile):  
        """  
        手牌＋和了牌と面子＋雀頭の牌が完全に一致しているか確認する。  
        """  
        full_hand = hand + [winning_tile]  
        full_hand_counter = Counter(full_hand)  
  
        # 面子＋雀頭の牌をカウント  
        melds_pairs_counter = Counter()  
        for meld in melds:  
            melds_pairs_counter.update(meld)  
        for pair in pairs:  
            melds_pairs_counter.update(pair)  
  
        # カウントが一致する場合のみ有効  
        return full_hand_counter == melds_pairs_counter  
  
    def find_necessary_tiles(hand, melds, pairs):  
        """  
        和了牌を探索する。  
        """  
        necessary_tiles = set()  
        for tile in range(1, 10):  # 萬子の範囲  
            if is_valid_combination(hand, melds, pairs, tile):  
                necessary_tiles.add(tile)  
        return necessary_tiles  
  
    results = []  
    backtrack(hand, [], [])  
    final_results = []  
  
    for melds, pairs in results:  
        necessary_tiles = find_necessary_tiles(hand, melds, pairs)  
        if necessary_tiles:  # 和了牌が存在する場合のみ結果に追加  
            final_results.append((melds, pairs, necessary_tiles))  
  
    return final_results  
  
# テストデータ  
hand = [1, 1, 1, 2, 2, 2, 3, 3, 3, 8, 9, 9, 9]  
winning_patterns = find_winning_patterns(hand)  
  
# 結果を表示  
print(f"手牌: {hand}")  
for pattern in winning_patterns:  
    melds, pairs, necessary_tiles = pattern  
    print("面子:", melds, "雀頭:", pairs, "和了牌:", necessary_tiles)  