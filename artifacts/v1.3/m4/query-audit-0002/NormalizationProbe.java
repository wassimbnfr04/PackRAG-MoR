import java.nio.file.*; import java.util.*; import java.text.Normalizer;
public class NormalizationProbe {
 public static void main(String[] args) throws Exception {
  for(String line: Files.readAllLines(Path.of(args[0]))) {
   String x=new String(Base64.getDecoder().decode(line),java.nio.charset.StandardCharsets.UTF_8);
   x=Normalizer.normalize(x,Normalizer.Form.NFKC).replace("\u0640","").replaceAll("[\u064b-\u065f\u0670]","").toLowerCase(Locale.ROOT)
    .replaceAll("[\\u0009-\\u000d\\u001c-\\u0020\u0085\u00a0\u1680\u2000-\u200a\u2028\u2029\u202f\u205f\u3000]+"," ").replaceAll("^ +| +$","");
   System.out.println(Base64.getEncoder().encodeToString(x.getBytes(java.nio.charset.StandardCharsets.UTF_8)));
  }
 }
}