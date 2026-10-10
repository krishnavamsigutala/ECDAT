const crypto = require('crypto');

function hashPassword(pw) {
    return crypto.createHash('md5').update(pw).digest('hex');
}

function encrypt(key, iv, data) {
    const cipher = crypto.createCipheriv('aes-256-gcm', key, iv);
    return cipher.update(data);
}
