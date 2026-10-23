import java.util.*;
import org.packrag.model.*;
public class BlankProbe {
 public static void main(String[] args) {
  for(int point : new int[]{9,10,11,12,13,28,29,30,31,32,133,160,5760,8192,8193,8194,8195,8196,8197,8198,8199,8200,8201,8202,8232,8233,8239,8287,12288}) {
   String value=new String(Character.toChars(point));
   DerivedText row=new DerivedText("c","generator","en","74 °C.","c9352463465208c006e9604385d46db6075f99f74b016f0444ba9359e98ba7a9","official_translation",value,null,null);
   String state;
   try { GeneratorRepresentations.INSTANCE.select("Source.","a1484bf1466bbed0de88d9790a20f5d511798a8eed0dbaac2f9b912728f42250","fr",Collections.singletonList(row));state="ACCEPTED"; }
   catch(RepresentationFailure error) { state=error.getState(); }
   System.out.println(point+"\t"+kotlin.text.StringsKt.isBlank(value)+"\t"+state);
  }
 }
}