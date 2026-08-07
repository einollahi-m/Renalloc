const CREG_GROUPS={A1C:['A1','A3','A11','A19','A29','A30','A31','A36','A80'],A2:['A2','A9','A23','A24','A28','A68','A69','B17','B57','B58'],A10C:['A10','A25','A26','A34','A66','A32','A33','A43','A74'],BW4:['A9','A23','A24','A25','A32','B13','B27','B37','B38','B44','B47','B49','B51','B52','B53','B57','B58','B59','B63','B67'],B5C:['B5','B51','B52','B18','B35','B53'],B5C2:['B5','B51','B52','B15','B62','B63','B71','B72','B75','B76','B77','B17','B57','B58','B21','B49','B50','B35','B53','B73','B78'],BW6:['B7','B8','B14','B18','B35','B39','B40','B60','B61','B41','B42','B45','B46','B48','B50','B54','B55','B56','B62','B64','B65','B67','B71','B72','B73','B75','B76'],B7C:['B7','B8','B13','B27','B41','B42','B47','B48','B54','B55','B56','B60','B61','B81'],B8C:['B8','B18','B38','B39','B64','B65'],B12C:['B12','B44','B45','B13','B37','B41','B47','B21','B49','B50','B40','B60','B61']}
const SCORE_FIELDS=['hla_a','hla_b','hla_c','hla_drb1','hla_dqb1']
const ALL_FIELDS=[...SCORE_FIELDS,'hla_drb']
export const lowResolution=value=>String(value||'').split(':')[0].toUpperCase()
const serotype=value=>{const match=String(value||'').toUpperCase().match(/^([AB])\*?0*(\d+)/);return match?`${match[1]}${Number(match[2])}`:null}
const groupsFor=value=>{const type=serotype(value);return type?Object.entries(CREG_GROUPS).filter(([,items])=>items.includes(type)).map(([name])=>name):[]}
function multisetMatches(left,right){const used=new Set();let count=0;left.forEach(value=>{const index=right.findIndex((other,i)=>!used.has(i)&&lowResolution(other)===lowResolution(value));if(index>=0){used.add(index);count++}});return count}
export function evaluateTemporaryCandidate(recipient,candidate){
  const recipientHla=recipient.hla||{}
  const antibodies=(recipient.anti_hla_tests?.[0]?.selections||[]).map(item=>item.antigen)
  const antibodyLow=new Set(antibodies.map(lowResolution))
  const recipientLow=new Set(ALL_FIELDS.flatMap(field=>recipientHla[field]||[]).map(lowResolution))
  const selfOverlapLow=new Set([...antibodyLow].filter(value=>recipientLow.has(value)))
  const activeCreg=new Set(antibodies.flatMap(groupsFor))
  let matches=0,maximum=0
  const loci={}
  SCORE_FIELDS.forEach(field=>{const recipientValues=recipientHla[field]||[],candidateValues=candidate[field]||[];const common=multisetMatches(recipientValues,candidateValues);matches+=common;maximum+=2;loci[field]={matches:common,maximum:2,recipient:recipientValues,temporary:candidateValues}})
  const candidateAlleles=ALL_FIELDS.flatMap(field=>candidate[field]||[])
  const allExactConflicts=candidateAlleles.filter(value=>antibodyLow.has(lowResolution(value)))
  const selfOverlapConflicts=allExactConflicts.filter(value=>selfOverlapLow.has(lowResolution(value)))
  const exactConflicts=allExactConflicts.filter(value=>!selfOverlapLow.has(lowResolution(value)))
  const cregPotential=candidateAlleles.filter(value=>!antibodyLow.has(lowResolution(value))&&groupsFor(value).some(group=>activeCreg.has(group))).map(value=>({antigen:value,groups:groupsFor(value).filter(group=>activeCreg.has(group))}))
  const percent=maximum?Math.round(matches/maximum*100):0
  return {...candidate,loci,matches,maximum,percent,exactConflicts,selfOverlapConflicts,cregPotential,status:exactConflicts.length?'incompatible':selfOverlapConflicts.length||cregPotential.length?'conditional':'compatible'}
}
export function evaluateTemporaryCandidates(recipient,candidates){return candidates.map(candidate=>evaluateTemporaryCandidate(recipient,candidate)).sort((a,b)=>b.percent-a.percent)}
