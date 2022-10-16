// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

/**
  * @title Blockchain Morra Environment
  * @author Pritkumar Godhani(19CS10048), Debanjan Saha(19CS30014)
  * a smart-contract based environment to support 2-player Morra(Guess the Number) Game
  * Deploy Transaction : 0x50ccd933954fa7e7289ea13b97c20b16cc72d4fa24e0054446f2e6cde2089818
  * Smart Contract Address : 0x6545258742DF3aD620cE373B53529108f6358F1d
  * Confirmed in block#7773389; txIndex#2; goerli testnet
  */
contract Morra {

    bool isGameInit; // Denotes whether game is initalized or not
    int constant REVEAL_ERR = -1;

    uint private constant minBetAmt = 1000000 gwei;
    string private constant NO_REVEAL = "";

    struct Player{
        address payable playerAddr; // address of the player
        uint256 betAmount; // Amount bid by the player
        bytes32 committedMoveHash; // hash of the move committed by the player
        string revealedMove; // move revealed by the player
        uint8 status; // 0 => Start State, 1 => Move Committed, 2=> Move Revealed
    }

    Player[] public players; // Stores a dynamic array of the players
    // Player[] public currentPlayers; 

    function initialize() public payable returns (uint) {
        require(msg.value >= minBetAmt, "Minimum bet amount is 0.001ETH.");

        if(!isGameInit) { 

            delete players;
            
            // push player 1 in currentPlayers and players
            players.push(Player(payable(msg.sender), msg.value, "", NO_REVEAL, 0));
            
            // currentPlayers.push(Player(msg.sender, msg.value, "", NO_REVEAL));
            
            isGameInit = true;
            return 1;
        } else if(isGameInit && players.length == 1) {
            require(msg.sender != players[0].playerAddr, "Cannot bet against oneself.");
            require(msg.value >= players[0].betAmount, "Bet amount should be more than the registered amount by first player.");
            
            // push player 2 in currentPlayers only
            players.push(Player(payable(msg.sender), msg.value, "", NO_REVEAL, 0));

            return 2;
        } else {
            return 0;
        }
    }

    function commitmove(bytes32 hashMove) public returns (bool) {
        // check if all players registered
        require(players.length == 2, "Only two players must be registered.");

        // check if sender is one of player 1 or 2
        require(players[0].playerAddr == msg.sender || players[1].playerAddr == msg.sender, "Please register before submitting move.");
        
        // get sender's playerId
        uint playerId = getPlayerId()-1;

        // check commit status
        if(players[playerId].status != 0) {
            return false;
        }

        // save the hash value; update status
        players[playerId].committedMoveHash = hashMove;
        players[playerId].status = 1;

        // return success
        return true;        
    }


    function revealmove(string memory revealedMove) public returns (int) {
        require(players.length == 2, "Not enough players joined yet");
        require(msg.sender == players[0].playerAddr || msg.sender == players[1].playerAddr, "Attack detected! RevealMove requested from unknown player");
        require(players[0].status >= 1 && players[0].status >= 1, "Please wait! Both players have not yet committed their move");

        uint playerId = getPlayerId()-1;
       
        if(players[playerId].status != 1){
            return REVEAL_ERR;
        }

        bytes32 hashedMove = sha256(abi.encodePacked(revealedMove));
        if(players[playerId].committedMoveHash != hashedMove){
            return REVEAL_ERR;
        }else{
            players[playerId].revealedMove = revealedMove;
            players[playerId].status = 2;
        }

        if(players[0].status == 2 && players[1].status == 2){
            int player1Move = getFirstChar(players[0].revealedMove);
            int player2Move = getFirstChar(players[1].revealedMove);
            uint winner = ((player1Move == player2Move) ? 1 : 0);
            payWinner(winner);
            deinit();      
        }
        return getFirstChar(revealedMove);      
    }

    // Helper Function
    function getFirstChar(string memory str) private pure returns (int) {
        if (bytes(str)[0] == 0x30) {
            return 0;
        } else if (bytes(str)[0] == 0x31) {
            return 1;
        } else if (bytes(str)[0] == 0x32) {
            return 2;
        } else if (bytes(str)[0] == 0x33) {
            return 3;
        } else if (bytes(str)[0] == 0x34) {
            return 4;
        } else if (bytes(str)[0] == 0x35) {
            return 5;
        } else {
            return -1;
        }
    }

    function payWinner(uint playerId) public {
        require(getBalance() >= players[0].betAmount + players[1].betAmount, "Balance error. Bet amounts don't add.");
        require(playerId >= 0 && playerId <= 1, "Invalid playerId.");
        players[playerId].playerAddr.transfer(players[0].betAmount + players[1].betAmount);
    }   

    function deinit() public {
        players.pop();
        players.pop();
        isGameInit = false; 
    }

    function getBalance() public view returns (uint) {
        return address(this).balance;
    }

    function getPlayerId() public view returns (uint){
        uint playerId = 0;
        if(msg.sender == players[0].playerAddr) {
            playerId = 1;
        } else if(msg.sender == players[1].playerAddr) {
            playerId = 2;
        }
        return playerId;
    }
}
