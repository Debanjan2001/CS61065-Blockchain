// SPDX-License-Identifier: GPL-3.0

pragma solidity >=0.7.0 <0.9.0;

contract Morra{

    bool isGameInit; // Denotes whether game is initalized or not

    struct Player{
        address playerAddr; // address of the player
        uint256 betAmount; // Amount bid by the player
        bytes32 committedMoveHash; // hash of the move committed by the player
        uint8 revealedMove; // move revealed by the player
    }

    Player[] public players; // Stores a dynamic array of the players

    function revealmove(string memory revealedMove) public returns (int) {}

    function commitmove(bytes32 hashMove) public returns (bool) {}

    function initialize() public payable returns (uint) {}

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
}
