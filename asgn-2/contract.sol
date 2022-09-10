// SPDX-License-Identifier: GPL-3.0 
pragma solidity >=0.7.0 <0.9.0;

contract AddressRollMap {
    mapping(address => string) public roll;

    function update(string calldata newRoll) public {
        roll[msg.sender] = newRoll;
    }
    
    function get(address addr) public view returns (string memory) {
        return roll[addr];
    }
    
    function getmine() public view returns (string memory) {
        return roll[msg.sender];
    }
}