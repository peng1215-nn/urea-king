let currentGames = [];       // 所有进行中的牌局
let currentGameIndex = 0;    // 当前 tab 索引
let currentGame = null;      // 当前选中牌局
let currentPlayers = [];
let currentRequests = [];
let allGroupMembers = [];
let selectedAddPlayer = [];
let currentMeId = null;       // 当前登录的局头（一个组可以有两个局头，各自只能给自己买入）
