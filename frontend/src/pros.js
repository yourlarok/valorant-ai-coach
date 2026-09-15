// 主原型 key → 职业哥风格描述
export const PRO_STYLES = {
  headshot_machine: '打法画像接近 TenZ 式爆头决斗者',
  suicide_squad: '接近 aspas 式激进突破手',
  clutch_god: '接近 nAts 式残局大师',
  stable_pillar: '接近 Boaster 式团队支柱',
  econ_blackhole: '独一档的经济黑洞，职业圈找不到模板',
  utility_bot: '接近 Sova 专精哥式技能流',
  balanced_default: '风格尚未定型，职业选手模板待定',
}

// 后端 Archetype.title → key，供只拿到中文标题的调用方反查
const TITLE_TO_KEY = {
  '爆头机器': 'headshot_machine',
  '开局敢死队': 'suicide_squad',
  '残局之神': 'clutch_god',
  '定海神针': 'stable_pillar',
  '经济黑洞': 'econ_blackhole',
  '人形闪光弹': 'utility_bot',
  '六边形战士（毛坯版）': 'balanced_default',
}

export function proStyleFor(primary) {
  const key = primary in PRO_STYLES ? primary : TITLE_TO_KEY[primary]
  return PRO_STYLES[key] || PRO_STYLES.balanced_default
}
