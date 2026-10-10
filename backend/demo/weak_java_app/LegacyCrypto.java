import javax.crypto.Cipher;
import java.security.MessageDigest;

public class LegacyCrypto {
    // Weak: ECB mode leaks structure; SHA-1 is classically broken.
    public byte[] encryptRecord(byte[] data) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
        return cipher.doFinal(data);
    }

    public byte[] fingerprint(byte[] data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA1");
        return md.digest(data);
    }
}
