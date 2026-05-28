// 后端地址：开发时改为你的服务器 IP，上线时改为 HTTPS 域名
const API = 'http://localhost:8080'

const ICONS = { chicken: '🐔', duck: '🦆', beef: '🐂', shrimp: '🦐', fish: '🐟', lamb: '🐑' }

Page({
  data: {
    days: [],
    weekLabel: '',
    loading: true,
    error: ''
  },

  onLoad() {
    this.fetchMenu()
  },

  onPullDownRefresh() {
    this.fetchMenu().then(() => wx.stopPullDownRefresh())
  },

  fetchMenu() {
    const self = this
    const now = new Date()
    const day = now.getDay()
    const diff = now.getDate() - day + (day === 0 ? -6 : 1)
    const monday = new Date(now.getFullYear(), now.getMonth(), diff)
    const y = monday.getFullYear()
    const m = String(monday.getMonth() + 1).padStart(2, '0')
    const d = String(monday.getDate()).padStart(2, '0')
    const weekKey = y + '-' + m + '-' + d

    const dn = new Date(Date.UTC(monday.getFullYear(), monday.getMonth(), monday.getDate()))
    const dayNum = dn.getUTCDay() || 7
    dn.setUTCDate(dn.getUTCDate() + 4 - dayNum)
    const ys = new Date(Date.UTC(dn.getUTCFullYear(), 0, 1))
    const weekNum = Math.ceil((((dn - ys) / 86400000) + 1) / 7)
    const weekLabel = monday.getFullYear() + '年 第' + weekNum + '周'

    return new Promise((resolve) => {
      wx.request({
        url: API + '/api/menus?week_key=' + weekKey,
        success(res) {
          if (res.statusCode === 200 && res.data.days) {
            const days = res.data.days.filter(d => d.day_name !== '周六' && d.day_name !== '周日').map(day => {
              if (day.is_holiday) {
                return { isHoliday: true, dayName: day.day_name, dateStr: day.date.slice(5), date: day.date }
              }
              const d = day.dishes
              return {
                isHoliday: false,
                dayName: day.day_name,
                dateStr: day.date.slice(5),
                date: day.date,
                bigMeat: (d.bigMeat || []).map(m => ({ name: m.name, cuisine: m.cuisine, icon: ICONS[m.category] || '', isSichuan: m.cuisine === '川菜' })),
                otherMeat: (d.otherMeat || []).map(m => ({ name: m.name, cuisine: m.cuisine, isSichuan: m.cuisine === '川菜' })),
                vegetables: (d.vegetables || []).map(v => ({ name: v.name, cuisine: v.cuisine, isSichuan: v.cuisine === '川菜' })),
                soup: { name: d.soup ? d.soup.name : '', cuisine: d.soup ? d.soup.cuisine : '', isSichuan: d.soup && d.soup.cuisine === '川菜' },
                noodle: { name: d.noodle ? d.noodle.name : '', cuisine: d.noodle ? d.noodle.cuisine : '', isSichuan: d.noodle && d.noodle.cuisine === '川菜' }
              }
            })
            self.setData({ days, weekLabel, loading: false, error: '' })
          } else {
            self.setData({ loading: false, error: '暂无本周菜单' })
          }
          resolve()
        },
        fail() {
          self.setData({ loading: false, error: '加载失败，下拉刷新重试' })
          resolve()
        }
      })
    })
  }
})
