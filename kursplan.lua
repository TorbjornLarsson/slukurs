function Header(el)
    if el.content[1].text=="Kursplan" then
        return {}
    else
        return pandoc.Header(el.level-1, el.content)
    end
end
