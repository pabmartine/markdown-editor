const Web3 = require('web3');
const privateKey = '0x60e559ebade2215b9146caa7f290d0f9cddadd882e379c46879389704136d2e2';
const account = new Web3().eth.accounts.privateKeyToAccount(privateKey);
console.log('Address:', account.address);
