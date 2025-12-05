import random  
import define
import player
import tile_mountain
import kawa


#ドラ牌→実ドラの変換
def next_tile(tile):  
    # 数牌  
    if len(tile) == 2 and tile[1] in define.SUIT_ORDER:  
        num = int(tile[0])  
        return ('1' if num == 9 else str(num+1)) + tile[1]  
    # 字牌  
    honors = list(define.HORNOR_ORDER.keys())
    if tile in define.HORNOR_ORDER:  
        idx = honors.index(tile)  
        idx_next = (idx+1) % 7  
        return honors[idx_next]  
    return tile  

# プレイヤー名
player_names = ["あなた", "ＡＩ１", "ＡＩ２", "ＡＩ３"]

# 座席決定（名前順）
seat_player_order = [0, 1, 2, 3]
start_seat_plyaer_order = random.sample(seat_player_order, len(seat_player_order))

# seatの順でソート 
seats = list(define.SEATS)
seat_order = sorted(seats, key=lambda x: define.SEAT_ORDER[x])  
  
result = " ".join([f"{seat_order[i]}：{player_names[seat_player_no]}" for i, seat_player_no in enumerate(start_seat_plyaer_order)])
print("開始座席順： ", result)
print()

# 親決定
kari_oya = 0
print(f"仮仮親は{player_names[start_seat_plyaer_order[kari_oya]]}")
dice1 = 0
dice2 = 0
for i in range(2):
    dice1 = random.randint(1, 6)
    dice2 = random.randint(1, 6)
    kari_oya = (kari_oya + dice1 + dice2 -1) % define.PLAYER_MAX
    if i== 0:
        print(f"サイコロ1回目：{dice1}と{dice2} 仮親は{player_names[start_seat_plyaer_order[kari_oya]]}")
    else:
        print(f"サイコロ2回目：{dice1}と{dice2} 親は{player_names[start_seat_plyaer_order[kari_oya]]}")
print()

# プレイヤー作成
players = []
for i in range(define.PLAYER_MAX):
    order = start_seat_plyaer_order[(i + kari_oya) % define.PLAYER_MAX]
    players.append(player.Player(id=order, name=player_names[order], wind=seat_order[i]))
    players[i].clear_hand()

result = " ".join(f"{players[i].wind}：{players[i].name}" for i in range(define.PLAYER_MAX))
print("開始風順： ", result)
print()

# 牌山を作成
mountain = tile_mountain.TileMountain()
mountain.create_tile_mountain()
mountain.setting_dead_wall(dice1, dice2)

# 河作成
river = kawa.Kawa()

oya = 0

# 配牌処理
for round_num in range(3):  
    print(f"=== {round_num+1}回目の4枚ずつ配牌 ===")
    for i in range(define.PLAYER_MAX):
        idx = (oya + i) % define.PLAYER_MAX
        get_tiles = mountain.draw_tiles_from_wall(4)
        players[idx].add_hand(get_tiles)
        players[idx].show_hand_and_melds()
    print()  
  
print(f"=== 1枚ずつ配牌 ===")  
for i in range(define.PLAYER_MAX):  
    idx = (oya + i) % define.PLAYER_MAX
    get_tile = mountain.draw_tiles_from_wall(1)
    players[idx].add_hand(get_tile)
    players[idx].show_hand_and_melds()
print()  
  
print(f"=== 配牌整理 ===")  
for i in range(define.PLAYER_MAX):  
    idx = (oya + i) % define.PLAYER_MAX
    players[idx].sort_hand()
    players[idx].show_hand_and_melds()
print()  
  
print(f"=== 親が積る ===") 
tumo_tile = mountain.draw_one_tile()
players[oya].draw_tile(tumo_tile)
players[oya].show_hand_and_melds()
print()  
  
# ドラ表示牌 
mountain.set_initial_dora()
mountain.show_dora_indicators()

print()  
  