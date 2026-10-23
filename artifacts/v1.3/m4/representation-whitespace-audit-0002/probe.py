"""Measure real compiled Kotlin provenance predicate against pinned Python blanks."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from product.packrag.representations import select_representation
from product.packrag.config import RuntimeContractError
java=ROOT/'vendor/java/jdk-17.0.20.1+1/bin'
jars=list((ROOT/'.cache/gradle/caches/modules-2/files-2.1/org.jetbrains.kotlin/kotlin-stdlib/2.4.20').rglob('kotlin-stdlib-2.4.20.jar'));assert len(jars)==1
classes=ROOT/'product/android/core-model/build/intermediates/runtime_library_classes_dir/release/bundleLibRuntimeToDirRelease'
canonical='Source.';body='74 °C.';digest=lambda text:hashlib.sha256(text.encode()).hexdigest()
points=[p for p in range(0x110000) if chr(p).isspace()];assert len(points)==29
source='''import java.util.*;
import org.packrag.model.*;
public class BlankProbe {
 public static void main(String[] args) {
  for(int point : new int[]{POINTS}) {
   String value=new String(Character.toChars(point));
   DerivedText row=new DerivedText("c","generator","en","BODY","BODY_HASH","official_translation",value,null,null);
   String state;
   try { GeneratorRepresentations.INSTANCE.select("Source.","SOURCE_HASH","fr",Collections.singletonList(row));state="ACCEPTED"; }
   catch(RepresentationFailure error) { state=error.getState(); }
   System.out.println(point+"\\t"+kotlin.text.StringsKt.isBlank(value)+"\\t"+state);
  }
 }
}'''.replace('POINTS',','.join(map(str,points))).replace('BODY_HASH',digest(body)).replace('SOURCE_HASH',digest(canonical)).replace('BODY',body)
(HERE/'BlankProbe.java').write_text(source,encoding='utf-8')
classpath=str(classes)+';'+str(jars[0]);command=[str(java/'javac.exe'),'-encoding','UTF-8','-cp',classpath,str(HERE/'BlankProbe.java')]
compiled=subprocess.run(command,capture_output=True,check=True);(HERE/'compiler.txt').write_bytes(compiled.stdout+compiled.stderr)
executed=subprocess.run([str(java/'java.exe'),'-cp',str(HERE)+';'+classpath,'BlankProbe'],capture_output=True,check=True)
(HERE/'original-jvm-output.txt').write_bytes(executed.stdout+executed.stderr)
rows=[]
for line in executed.stdout.decode().splitlines():
    point,blank,state=line.split('\t');point=int(point)
    source_row=dict(canonical_text=canonical,text_sha256=digest(canonical),language='fr')
    derived=dict(purpose='generator',language='en',text=body,text_sha256=digest(body),derivation_method='official_translation',derivation_source=chr(point),reviewer_id=None,reviewed_at=None)
    try:select_representation(source_row,[derived]);python='ACCEPTED'
    except RuntimeContractError as error:python=str(error)
    rows.append(dict(point=point,python_blank=True,kotlin_blank=blank=='true',python_state=python,kotlin_state=state))
mismatches=[r for r in rows if r['python_state']!=r['kotlin_state']]
record=dict(status='OBSERVED_PARITY_MISMATCH_D2_ACCEPTANCE_HELD' if mismatches else 'PASS_NO_MISMATCH',scope='CURRENT_COMPILED_KOTLIN_CORE_AND_STDLIB_HOST_NOT_DEVICE_IMPORT_OR_GENERATION',
    cases=rows,mismatches=mismatches,commands=[command],java_version=subprocess.check_output([str(java/'java.exe'),'-version'],stderr=subprocess.STDOUT).decode(),
    compiled_core_sha256=hashlib.sha256((classes/'org/packrag/model/GeneratorRepresentations.class').read_bytes()).hexdigest(),
    kotlin_stdlib_sha256=hashlib.sha256(jars[0].read_bytes()).hexdigest())
(HERE/'audit.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(dict(status=record['status'],mismatches=mismatches)))
