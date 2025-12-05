import define

class Player:  
    def __init__(self, id, name, wind, score=25000):  
        self.id = id                    # プレイヤーID（0-3）
        self.name = name                # プレイヤーの名前  
        self.wind = wind                # プレイヤーの風（東・南・西・北）  
        self.score = score              # プレイヤーの持ち点（初期値は25000点）  
        self.hand = []                  # 手持ちの牌（鳴いた面子と自摸牌を除く）
        self.tsumo_tile = None          # 自摸牌 (現在のツモ牌)  
        self.melds = []                 # 鳴いた面子 (ポン・チー・カンなど)  
        self.discard_tile = None        # 現在の捨て牌 (最後に捨てた牌)  
        self.riichi_kawa_tile_no = -1   # リーチしたときの河牌番号 (-1はリーチしていないことを示す)

    # 手牌、鳴き、河、ツモ牌をリセット
    def clear_hand(self):
        """手牌、鳴き、河、ツモ牌をリセット"""  
        self.hand = []  
        self.tsumo_tile = None  
        self.melds = []  
        self.discard_tile = None  

    # 初期配牌として牌を手牌に追加
    def add_hand(self, tiles):  
        """初期配牌として牌を手牌に追加"""  
        self.hand.extend(tiles)
  
    def draw_tile(self, tile):  
        """牌を引く (ツモ牌として保持)"""  
        self.tsumo_tile = tile 
        print(f"{self.name}が{tile}をツモしました。")

    #手牌整理（ソート）
    def sort_hand(self):  
        def tile_key(tile):
            # 数牌  
            if len(tile) == 2 and tile[1] in define.SUIT_ORDER:  
                num = int(tile[0])  
                suit = tile[1]  
                return (0, define.SUIT_ORDER[suit], num)  
            # 字牌  
            elif tile in define.HORNOR_ORDER:  
                return (1, define.HORNOR_ORDER[tile], 0)  
            else:  
                return (2, 100, 0)  # 未知牌があっても最後に回す  
      
        self.hand = sorted(self.hand, key=tile_key) 

    def add_tsumo_to_hand(self):  
        """ツモ牌を手牌に追加"""  
        if self.tsumo_tile:  
            self.hand.append(self.tsumo_tile)  
            self.sort_hand()
            self.tsumo_tile = None  # ツモ牌をリセット 

    def discard_tile(self, tile, from_tsumo=False):  
        """  
        牌を捨てる (手牌または自摸牌から捨てる)  
        :param tile: 捨てる牌  
        :param from_tsumo: 自摸牌から捨てる場合は True, 手牌から捨てる場合は False  
        """  
        if from_tsumo:  
            # 自摸牌から捨てる処理  
            if self.tsumo_tile == tile:  
                self.discard_tile = tile    # 捨て牌を更新
                self.tsumo_tile = None  # 自摸牌をリセット  
                print(f"{self.name}が自摸牌 {tile} を捨てました。")  
            else:  
                print(f"{self.name}の自摸牌は {self.tsumo_tile} ですが、{tile} を捨てようとしています。処理を中断します。")  
        else:  
            # 手牌から捨てる処理  
            if tile in self.hand:  
                self.hand.remove(tile)    
                self.discard_tile = tile    # 捨て牌を更新
                print(f"{self.name}が手牌 {tile} を捨てました。")  
            else:  
                print(f"{tile} は {self.name} の手牌に存在しません。処理を中断します。")

    def can_meld(self, discard_tile, from_player_id, is_left_player=False):  
        """  
        手牌から鳴けるかを判定し、鳴く際の面子情報を返す  
        :param discard_tile: 他のプレイヤーが捨てた牌  
        :param from_player_id: 捨て牌を出したプレイヤーのID  
        :param is_left_player: チーが可能かどうか (左のプレイヤーか判定)  
        :return: 鳴ける場合は可能なアクションと面子情報のリストを返す  
                 例: [{"type": "ポン", "meld": ["5萬", "5萬", "5萬"], "from_player": 2}]  
        """  
        meld_actions = []  
  
        # ポンの判定  
        if self.hand.count(discard_tile) >= 2:  
            meld = [discard_tile] * 3  # ポンの面子は捨て牌 + 同じ牌2枚  
            meld_actions.append({"type": define.MELD_TYPE_PON, "meld": meld, "from_player": from_player_id})  
  
        # カンの判定  
        if self.hand.count(discard_tile) == 3:  
            meld = [discard_tile] * 4  # カンの面子は捨て牌 + 同じ牌3枚  
            meld_actions.append({"type": define.MELD_TYPE_KAN, "meld": meld, "from_player": from_player_id})  
  
        # チーの判定（左のプレイヤーの捨て牌に対してのみ可能）  
        if is_left_player:  
            try:  
                discard_value = int(discard_tile[:-1])  # 数字部分を取得  
                suit = discard_tile[-1]  # 萬子, 筒子, 索子などを取得  
  
                # チーの可能な組み合わせ  
                potential_chis = [  
                    [f"{discard_value - 2}{suit}", f"{discard_value - 1}{suit}"],  
                    [f"{discard_value - 1}{suit}", f"{discard_value + 1}{suit}"],  
                    [f"{discard_value + 1}{suit}", f"{discard_value + 2}{suit}"],  
                ]  
  
                # 手牌にあるかどうかを確認  
                for chi in potential_chis:  
                    if all(tile in self.hand for tile in chi):  
                        meld = chi[:]  
                        meld.insert(1, discard_tile)  # 捨て牌を順子の真ん中に挿入  
                        meld_actions.append({"type": default.MELD_TYPE_CHI, "meld": meld, "from_player": from_player_id})  
            except ValueError:  
                # 字牌の場合はチーできないため無視  
                pass  
  
        return meld_actions  
  
    def make_meld(self, meld_info):  
        """  
        鳴きを実行する  
        :param meld_info: 鳴きの情報 (can_meld から取得する辞書形式のデータ)  
                          例: {"type": "ポン", "meld": ["5萬", "5萬", "5萬"], "from_player": 2}  
        """  
        meld_type = meld_info["type"]           # 鳴きの種類 ("ポン", "チー", "カン")  
        meld_tiles = meld_info["meld"]          # 鳴きで使用する牌のリスト  
        from_player = meld_info["from_player"]  # 捨て牌を出したプレイヤー番号  
  
        # 鳴きで使用する牌を手牌から削除  
        for tile in meld_tiles:  
            if tile != meld_tiles[0]:  # 捨て牌は手牌に含まれないのでスキップ  
                self.hand.remove(tile)  
  
        # 鳴いた面子を記録  
        self.melds.append({  
            "type": meld_type,  
            "tiles": meld_tiles,  
            "from_player": from_player  
        })  
  
        print(f"{self.name}が{meld_type}を実行しました: {meld_tiles}")  

    def get_tiles(self, include_tsumo=False):  
        """  
        手牌、ツモ牌、鳴いた面子を個別に取得  
        :param include_tsumo: ツモ牌を含めるかどうか (デフォルトは含めない)  
        :return: 辞書形式で返す { "hand": [...], "tsumo_tile": ..., "melds": [...] }  
        """  
        return {  
            "hand": self.hand,  
            "tsumo_tile": self.tsumo_tile if include_tsumo else None,  
            "melds": self.melds  
        }  

    def show_hand_and_melds(self):  
        """自分の手牌と鳴いた面子を1列で表示 (誰の牌を鳴いたかを含む)"""  
        # 手牌を表示 (手牌そのまま)  
        hand_display = f"[" + ", ".join(self.hand) + f"]"  
  
        # 鳴いた面子を表示 (鳴いた種類、牌、鳴かれたプレイヤーを含む)  
        melds_display = " ".join([  
            f"[" + ", ".join(meld['tiles']) + f" (Player {meld['from_player']})]"  
            for meld in self.melds  
        ])  

        tumo_display = f" [ツモ牌: {self.tsumo_tile}]" if self.tsumo_tile else ""
  
        # 全体を1列で表示  
        print(f"{self.name}の状態: {hand_display} {melds_display} {tumo_display}") 

    def update_score(self, points):  
        """スコアを更新するメソッド"""  
        self.score += points  
  
    def __str__(self):  
        """プレイヤー情報を文字列として表示"""  
        return f"名前: {self.name}, 風: {self.wind}, 点数: {self.score}"  