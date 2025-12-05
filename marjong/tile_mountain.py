
import random  
import define

class TileMountain:
    def __init__(self):
        self.tiles = []
        self.wall_tiles = []

    # 牌山作成メイン関数
    def create_tile_mountain(self):
        self.make_tiles()
        self.mixing_tiles()
        self.make_wall_tiles()

    # 王牌設定メイン関数
    def setting_dead_wall(self, dice1, dice2):
        self.set_dead_wall(dice1, dice2)
        self.set_initial_dora()

    # 槓ドラ追加＆嶺上自摸取得メイン関数
    def kang_tile_mountain(self):
        self.add_kang_dora()
        kan_tile = self.rinshan_tsumo()
        self.add_tile_to_dead_wall()
        return kan_tile
		
    # 牌生成関数  
    def make_tiles(self):
        self.tiles = [] # 牌リスト初期化

        # 牌の生成
        numbers = [str(i) for i in range(1, 10)]  
        for suit in define.SUITS:  
            for num in numbers:  
                self.tiles.extend([num + suit] * define.ONE_TILE_MAX)  
        for honor in define.HORNORS:  
            self.tiles.extend([honor] * define.ONE_TILE_MAX) 
            
    # 洗牌関数
    def mixing_tiles(self):  
        random.shuffle(self.tiles)

    # 牌山作成関数
    def make_wall_tiles(self):
        for i, tile in enumerate(self.tiles):  
            seat_id = i                                     # 席ID（0～3）  
            index_in_seat = i % define.WALL_TILES_PER_SEAT  # 席毎での並び順（0～33）  
            column = index_in_seat // 2                     # 列番号（0～16）
            is_top = (index_in_seat % 2 == 0)               # 上段か下段かを設定 
          
            # 牌情報を作成  
            self.wall_tiles.append({  
                "tile": tile,  
                "seat_id": seat_id,  
                "index_in_seat": index_in_seat,  
                "column": column,  
                "is_top": is_top,           # 上段か下段か  
                "is_dead_wall": False,       # 初期状態では王牌ではない 
                "is_dora_indicator": False  # 初期状態ではドラ表示牌ではない
            }) 

    # 王牌設定
    def set_dead_wall(self, dice1, dice2):  
        """
        サイコロの出目に基づいて王牌を設定する。  
      
        :param wall_tiles: 牌山（リスト形式）  
        :param dice1: サイコロ1の出目（1～6）  
        :param dice2: サイコロ2の出目（1～6）  
        :return: 王牌が設定された牌山  
        """  
        # サイコロの合計値を基に王牌の開始位置を計算  
        dice_sum = dice1 + dice2  
        split_position = (dice_sum * 2) % len(self.wall_tiles)  
      
        # 王牌部分を設定  
        for i in range(define.DEAD_WALL_SIZE):  
            index = (split_position + i) % len(self.wall_tiles)  
            self.wall_tiles[index]["is_dead_wall"] = True

    # 初期ドラ設定
    def set_initial_dora(self):  
        """wall_tiles 内でドラ表示牌を設定する。  """  
        # 王牌部分を抽出し、上段の牌のみ選択  
        upper_dead_wall_tiles = [  
            tile for tile in self.wall_tiles  
            if tile["is_dead_wall"] and tile["is_top"]  
        ]  

        # ドラ表示牌は上段の最後尾から3つ目の牌  
        if len(upper_dead_wall_tiles) >= 3:  
            dora_indicator = upper_dead_wall_tiles[-3]  # 最後尾から3つ目
            dora_indicator["is_dora_indicator"] = True  
        else:  
            raise ValueError("王牌の上段にドラ表示牌を設定できる牌がありません。")  

    # 槓ドラ追加
    def add_kang_dora(self):  
        """  槓が発生した際に槓ドラ表示牌を追加する（最後にドラになった牌の隣の牌を選択）。  """  
        # 王牌部分を抽出し、上段の牌のみ選択  
        upper_dead_wall_tiles = [  
            tile for tile in self.wall_tiles  
            if tile["is_dead_wall"] and tile["is_top"]  
        ]  
      
        # すでにドラ表示牌または槓ドラ表示牌になっている牌を探す  
        dora_tiles = [  
            tile for tile in upper_dead_wall_tiles  
            if tile.get("is_dora_indicator") or tile.get("is_kang_dora_indicator")  
        ]  
      
        if not dora_tiles:  
            raise ValueError("ドラ表示牌が設定されていません。槓ドラを設定できません。")  
  
        # 最後のドラ表示牌のインデックスを取得  
        last_dora_tile = dora_tiles[-1]  # 最後に選ばれたドラ牌  
        last_dora_index = upper_dead_wall_tiles.index(last_dora_tile)  
      
        # 隣の牌を槓ドラとして選択（次のインデックス）  
        next_kang_dora_index = last_dora_index + 1  
        if next_kang_dora_index < len(upper_dead_wall_tiles):  
            kang_dora_indicator = upper_dead_wall_tiles[next_kang_dora_index]  
            kang_dora_indicator["is_kang_dora_indicator"] = True  # 槓ドラとして設定  
        else:  
            raise ValueError("槓ドラを設定できる牌がありません（王牌の上段が不足しています）。")  

    # 嶺上自摸
    def rinshan_tsumo(self):  
        """槓が発生した際に嶺上牌を取得する（王牌から最後尾の牌を取得）"""  
        # 王牌部分を抽出  
        dead_wall_tiles = [tile for tile in self.wall_tiles if tile["is_dead_wall"]]  
      
        # 嶺上牌は王牌の最後尾（インデックス -1）  
        if dead_wall_tiles:
            rinshan_tile = dead_wall_tiles.pop()  # 王牌から取り出す 
            if not rinshan_tile["is_kang_dora_indicator"]:
                self.wall_tiles.remove(rinshan_tile)  # 元のリストからも削除  
                return rinshan_tile  
            else:
                raise ValueError("王牌に嶺上牌がありません。")                  
        else:  
            raise ValueError("王牌に牌がありません。")  

    # 山牌から王牌に牌を追加（嶺上用）
    def add_tile_to_dead_wall(self):  
        """山牌から王牌に牌を追加する。"""  
        # 山牌部分を抽出（まだ使用されていない牌）  
        remaining_tiles = [tile for tile in self.wall_tiles if not tile["is_dead_wall"]]  
      
        # 追加する牌は山牌の先頭（インデックス 0）  
        if remaining_tiles:  
            new_dead_wall_tile = remaining_tiles[0]  
            new_dead_wall_tile["is_dead_wall"] = True  # 王牌に設定  
        else:  
            raise ValueError("山牌に牌がありません。")
            
    # 山から指定個数の牌を取り出して削除（配牌用）
    def draw_tiles_from_wall(self, count):  
        """  
        山から指定個数の牌を取り出して山から削除する。  
        取り出す牌は王牌の最後の牌の次から開始する。
  
        :param count: 取り出す牌の個数  
        :return: 取り出した牌のtileのみを含む配列  
        """  
        # 王牌の牌を抽出  
        dead_wall_tiles = [tile for tile in self.wall_tiles if tile.get("is_dead_wall", True)]  
  
        if not dead_wall_tiles:  
            raise ValueError("王牌が存在しません。")  
  
        # 王牌の最後の牌の次のインデックスを計算  
        last_dead_wall_index = self.wall_tiles.index(dead_wall_tiles[-1])  
        start_index = last_dead_wall_index + 1  
  
        # 山全体の長さ  
        wall_length = len(self.wall_tiles)  
  
        # 循環して牌を取り出す  
        drawn_tiles = []  
        for i in range(count):  
            current_index = (start_index + i) % wall_length  # 循環するインデックス  
            drawn_tiles.append(self.wall_tiles[current_index])  
  
        # 山から取り出した牌を削除  
        for tile in drawn_tiles:  
            self.wall_tiles.remove(tile)  
  
        # 取り出した牌のtile情報だけを返す  
        return [tile["tile"] for tile in drawn_tiles]  

    # 自摸牌取得
    def draw_one_tile(self):  
        """  
        山（wall）から1枚の牌を取り出して山から削除する。  
        取り出す牌は王牌を除外した部分の最初から開始し、山の最後に達した場合は循環する。  
        王牌しか残っていない場合はNoneを返す。  
  
        :return: 取り出した牌のtile（文字列）、またはNone（王牌しか残っていない場合）  
        """  
        # 王牌の牌を抽出  
        dead_wall_tiles = [tile for tile in self.wall_tiles if tile.get("is_dead_wall", False)]  
  
        if not dead_wall_tiles:  
            raise ValueError("王牌が存在しません。")  
  
        # 王牌の最後の牌の次のインデックスを計算  
        last_dead_wall_index = self.wall_tiles.index(dead_wall_tiles[-1])  
        start_index = last_dead_wall_index + 1  
  
        # 山全体の長さ  
        wall_length = len(self.wall_tiles)  
  
        # 循環して牌を取り出す  
        for i in range(wall_length):  
            current_index = (start_index + i) % wall_length  # 循環するインデックス  
            tile = self.wall_tiles[current_index]  
            if not tile.get("is_dead_wall", False):  # 王牌でない牌を取り出す  
                self.wall_tiles.remove(tile)  # 山から削除  
                return tile["tile"]  
  
        # 王牌しか残っていない場合はNoneを返す  
        return None

    # 残り自摸が可能な牌数（整数）
    def count_drawable_tiles(self):  
        """  
        山（wall）の中で自摸が可能な牌数を返す。  
        王牌（is_dead_wall=True）の牌は除外する。  
  
        :return: 自摸が可能な牌数（整数）  
        """  
        # 自摸可能な牌をカウント（is_dead_wall=False の牌のみ）  
        drawable_tiles = [tile for tile in self.wall_tiles if not tile.get("is_dead_wall", False)]  
        return len(drawable_tiles)  

    # ドラ表示牌のリストの取得
    def get_dora_indicators(self):  
        """  
        山（wall）からドラとなる牌をすべて取得する。  
  
        :return: ドラ牌のtileのみを含むリスト  
        """  
        # ドラ表示牌を抽出  
        dora_indicators = [  
            tile["tile"] for tile in self.wall_tiles  
            if tile.get("is_dora_indicator", True)  
        ]  
  
        # ドラ表示牌のtile情報のみを返す  
        return dora_indicators
    
    # 裏ドラ表示牌のリストの取得
    def get_ura_dora_indicators(self, dora_columns):  
        """  
        山（wall）から裏ドラの表示牌を取得する。  
        裏ドラ表示牌はドラ表示牌と同じ列（column）の下段の牌。  
  
        :return: 裏ドラ牌のtileのみを含むリスト  
        """  
        # ドラ表示牌を抽出  
        dora_tiles = [  
            tile for tile in self.wall_tiles  
            if tile.get("is_dora_indicator", True)  
        ]  
  
        # 裏ドラ候補を抽出（同じ列で下段の牌）  
        ura_dora_indicators = [  
            tile["tile"] for tile in self.wall_tiles  
            if tile.get("column") in dora_tiles and not tile.get("is_top", True)  
        ]  
  
        # 裏ドラ牌を返す  
        return ura_dora_indicators

    # ドラ表示牌を表示
    def show_dora_indicators(self):
        """ドラ表示牌を表示する。"""
        dora_indicators = self.get_dora_indicators()
        print("ドラ表示牌：", ", ".join(dora_indicators))