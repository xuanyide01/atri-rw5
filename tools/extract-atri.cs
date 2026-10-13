using System;using System.IO;using System.Linq;using System.Collections;using System.Collections.Generic;using System.Web.Script.Serialization;using System.IO.Compression;using System.Text;using GameRes.Formats.KiriKiri;
public static class ExtractAtri {
 static JavaScriptSerializer json=new JavaScriptSerializer {MaxJsonLength=100000000};
 static uint Adler(byte[] b){uint a=1,c=0;foreach(byte v in b){a=(a+v)%65521;c=(c+a)%65521;}return (c<<16)|a;}
 static byte[] ReadExact(Stream s,int n){var b=new byte[n];int p=0;while(p<n){int k=s.Read(b,p,n-p);if(k==0)throw new EndOfStreamException();p+=k;}return b;}
 public static void Run(string root,string manifest,string scheme,string output,string mode) {
  var s=json.Deserialize<Dictionary<string,object>>(File.ReadAllText(scheme));
  var cfg=new CxScheme {Mask=Convert.ToUInt32(s["m_mask"]),Offset=Convert.ToUInt32(s["m_offset"]),PrologOrder=((ArrayList)s["PrologOrder"]).Cast<object>().Select(Convert.ToByte).ToArray(),OddBranchOrder=((ArrayList)s["OddBranchOrder"]).Cast<object>().Select(Convert.ToByte).ToArray(),EvenBranchOrder=((ArrayList)s["EvenBranchOrder"]).Cast<object>().Select(Convert.ToByte).ToArray(),ControlBlock=((ArrayList)s["ControlBlock"]).Cast<object>().Select(Convert.ToUInt32).ToArray()};
  var cipher=new CxEncryption(cfg);var entries=json.Deserialize<List<Dictionary<string,object>>>(File.ReadAllText(manifest));var reports=new List<object>();int done=0;
  string[] textExt={".scn",".ks",".tjs",".txt",".csv",".ini",".stage",".stand",".sinfo",".pbd",".asd",".func",".event"};
  foreach(var e in entries){string name=(string)e["resolvedName"],arc=(string)e["archive"],ext=Path.GetExtension(name).ToLowerInvariant();
   if(mode=="scripts"&&!textExt.Contains(ext))continue;
   if(mode=="images"&&!new[]{".png",".jpg",".tlg",".pimg"}.Contains(ext))continue;
   string dest=Path.GetFullPath(Path.Combine(output,Path.GetFileNameWithoutExtension(arc),name.Replace('/',Path.DirectorySeparatorChar)));
   if(!dest.StartsWith(Path.GetFullPath(output)+Path.DirectorySeparatorChar,StringComparison.OrdinalIgnoreCase))throw new Exception("Unsafe resource path");
   byte[] raw;
   using(var f=File.OpenRead(Path.Combine(root,arc)))using(var combined=new MemoryStream()){
    foreach(ArrayList seg in (ArrayList)e["segments"]){f.Position=Convert.ToInt64(seg[1]);byte[] b=ReadExact(f,Convert.ToInt32(seg[3]));
     if((Convert.ToInt32(seg[0])&1)!=0){using(var input=new MemoryStream(b,2,b.Length-6))using(var z=new DeflateStream(input,CompressionMode.Decompress))using(var decoded=new MemoryStream()){z.CopyTo(decoded);b=decoded.ToArray();}}
     if(b.Length!=Convert.ToInt32(seg[2]))throw new Exception("Segment size: "+name);combined.Write(b,0,b.Length);
    }raw=combined.ToArray();
   }
   if(raw.Length!=Convert.ToInt32(e["original"]))throw new Exception("Entry size: "+name);
   uint hash=Convert.ToUInt32(e["adler"]);
   if(Convert.ToUInt32(e["flags"])!=0&&Adler(raw)!=hash)cipher.Decrypt(new Xp3Entry{Hash=hash},0,raw,0,raw.Length);
   if(Adler(raw)!=hash)throw new Exception("Adler mismatch: "+name);
   Directory.CreateDirectory(Path.GetDirectoryName(dest));File.WriteAllBytes(dest,raw);
   if(raw.Length>=5&&raw[0]==254&&raw[1]==254&&raw[2]==1){var chars=new char[(raw.Length-5)/2];for(int i=0;i<chars.Length;i++){int v=raw[5+i*2]|raw[6+i*2]<<8;chars[i]=(char)(((v&0xaaaa)>>1)|((v&0x5555)<<1));}File.WriteAllText(dest+".utf8.txt",new string(chars),new UTF8Encoding(false));}
   reports.Add(new{name=name,archive=arc,bytes=raw.Length,adlerVerified=true});done++;if(done%100==0)Console.WriteLine("EXTRACTED "+done+" "+name);
  }
  File.WriteAllText(Path.Combine(output,"extraction-"+mode+".json"),json.Serialize(reports),new UTF8Encoding(false));Console.WriteLine("VERIFIED "+done+" "+mode+" resources");
 }
}
