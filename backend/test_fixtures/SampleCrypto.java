import javax.crypto.Cipher;
import java.security.MessageDigest;
import java.security.KeyPairGenerator;

public class SampleCrypto {
    public byte[] weakEncrypt(byte[] data) throws Exception {
        Cipher cipher = Cipher.getInstance("AES/ECB/PKCS5Padding");
        return cipher.doFinal(data);
    }

    public byte[] weakHash(byte[] data) throws Exception {
        MessageDigest md = MessageDigest.getInstance("SHA1");
        return md.digest(data);
    }

    public void genKeys() throws Exception {
        KeyPairGenerator kpg = KeyPairGenerator.getInstance("RSA");
        kpg.initialize(2048);
    }
}
