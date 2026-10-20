export const autoSpeeds=['慢速','标准','快速'];
// Wait after the last glyph, allowing extra reading time for long paragraphs.
export function autoWait(speed,length){
  const base=[2600,1500,800][speed]||1500;
  return base+Math.min(5000,Math.max(0,length-60)*55);
}
