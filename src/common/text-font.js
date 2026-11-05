const extra="≪≫♪・呣蹡齁";
export function textFont(text){const value=String(text||'');for(let i=0;i<extra.length;i++)if(value.indexOf(extra[i])>=0)return 'atrifont';return '';}
