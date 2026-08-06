const escapeXml=value=>String(value??'').replace(/[<>&"']/g,char=>({"<":"&lt;",">":"&gt;","&":"&amp;",'"':"&quot;","'":"&apos;"}[char]))

export function exportExcelTable(filename, sheetName, headers, rows){
  const rowXml=[headers,...rows].map(row=>`<Row>${row.map(value=>`<Cell><Data ss:Type="String">${escapeXml(value)}</Data></Cell>`).join('')}</Row>`).join('')
  const workbook=`<?xml version="1.0" encoding="UTF-8"?><?mso-application progid="Excel.Sheet"?><Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet" xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet"><Worksheet ss:Name="${escapeXml(sheetName)}"><Table>${rowXml}</Table></Worksheet></Workbook>`
  const url=URL.createObjectURL(new Blob(['\uFEFF',workbook],{type:'application/vnd.ms-excel;charset=utf-8'}))
  const link=document.createElement('a');link.href=url;link.download=filename.endsWith('.xls')?filename:`${filename}.xls`;link.click();URL.revokeObjectURL(url)
}
