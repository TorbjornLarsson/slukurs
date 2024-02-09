local grat = true
local syllprev = false

function Header(el)
        strel = pandoc.utils.stringify(el)
        if (strel=="Kursplan") or (strel=="Syllabus") then
                syllhead = true
                syllprev = true
        else
                syllhead = false
        end
        if (el.level==2) then 
                if syllhead then
                        grat = false
                        return {}
                else
                        grat = true
                        return {}
                end
        elseif grat or syllhead then
                return {}
        elseif syllprev then
                syllprev = false
                return {}
        else
                return pandoc.Header(el.level-2, el.content)
        end
end

function Para(el)
        if grat then
                return {}
        end
end

function Plain(el)
        if grat then
                return {}
        end
end
