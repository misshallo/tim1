//@version=5
indicator("Multi Kernel Regression [ChartPrime]", overlay = true, max_lines_count = 500, max_bars_back = 500, max_labels_count = 500)

repaint = input.bool(true, "Repaint")

kernel = input.string("Laplace", "Kernel Select", 
 [ "Triangular"
 , "Gaussian"
 , "Epanechnikov"
 , "Logistic"
 , "Log Logistic"
 , "Cosine"
 , "Sinc"
 , "Laplace"
 , "Quartic"
 , "Parabolic"
 , "Exponential"
 , "Silverman"
 , "Cauchy"
 , "Tent"
 , "Wave"
 , "Power"
 , "Morters"])

bandwidth = input.int(14, 'Bandwidth', 1)
source = input.source(close, 'Source')
deviations = input.float(2.0, 'Deviation', 0, 100, 0.25, inline = "dev")
style = input.string("Solid", "Line Style", ["Solid", "Dotted", "Dashed"])
enable = input.bool(false, "", inline = "dev")
label_size = input.string("Tiny", "Labels", ["Auto", "Tiny", "Small", "Normal", "Large", "Huge"], inline = "label")
labels = input.bool(true, "", inline = "label")
bullish_color = input.color(color.rgb(84, 194, 148), "Colors", inline = "color")
bearish_color = input.color(color.rgb(235, 57, 57), "", inline = "color")
text_color = input.color(color.rgb(8, 12, 20), "", inline = "color")

size = switch label_size
    "Auto"   => size.auto
    "Tiny"   => size.tiny
    "Small"  => size.small
    "Normal" => size.normal
    "Large"  => size.large
    "Huge"   => size.huge

line_style = switch style 
    "Solid"  => line.style_solid
    "Dotted" => line.style_dotted
    "Dashed" => line.style_dashed

sq(source) => math.pow(source, 2)

gaussian(source, bandwidth) => 
    math.exp(-sq(source / bandwidth) / 2) / math.sqrt(2 * math.pi) 

triangular(source, bandwidth) =>
    math.abs(source/bandwidth) <= 1 ? 1 - math.abs(source/bandwidth) : 0.0

epanechnikov(source, bandwidth) =>
    math.abs(source/bandwidth) <= 1 ? (3/4.) * (1 - sq(source/bandwidth)) : 0.0

quartic(source, bandwidth) =>
    if math.abs(source/bandwidth) <= 1 
        15/16. * math.pow(1 - sq(source/bandwidth), 2)
    else
        0.0

logistic(source, bandwidth) =>
    1 / (math.exp(source / bandwidth) + 2 + math.exp(-source / bandwidth))

cosine(source, bandwidth) =>
    math.abs(source/bandwidth) <= 1 ? (math.pi / 4) * math.cos((math.pi / 2) * (source/bandwidth)) : 0.0

laplace(source, bandwidth) =>
    (1 / (2 * bandwidth)) * math.exp(-math.abs(source/bandwidth))

exponential(source, bandwidth) =>
    (1 / bandwidth) * math.exp(-math.abs(source/bandwidth))


silverman(source, bandwidth) =>
    if math.abs(source/bandwidth) <= 0.5 
        0.5 * math.exp(-(source/bandwidth)/2) * math.sin((source/bandwidth)/2 + math.pi/4) 
    else 
        0.0 

tent(source, bandwidth) =>
    if math.abs(source/bandwidth) <= 1
        1 - math.abs(source/bandwidth)
    else
        0.0

cauchy(source, bandwidth) =>
    1 / (math.pi * bandwidth * (1 + sq(source / bandwidth)))

sinc(source, bandwidth) =>
    if source == 0
        1
    else
        math.sin(math.pi * source / bandwidth) / (math.pi * source / bandwidth)

wave(source, bandwidth) =>
    if (math.abs(source/bandwidth) <= 1)
        (1 - math.abs(source/bandwidth)) * math.cos((math.pi * source) / bandwidth)
    else
        0.0

parabolic(source, bandwidth) =>
    if math.abs(source/bandwidth) <= 1
        1 - math.pow((source/bandwidth), 2)
    else
        0.0

power(source, bandwidth) =>
    if (math.abs(source/bandwidth) <= 1)
        math.pow(1 - math.pow(math.abs(source/bandwidth), 3), 3)
    else
        0.0

loglogistic(source, bandwidth) =>
    1 / math.pow(1 + math.abs(source / bandwidth), 2)

morters(source, bandwidth) =>
    if math.abs(source / bandwidth) <= math.pi
        (1 + math.cos(source / bandwidth)) / (2 * math.pi * bandwidth)
    else
        0.0

kernel(source, bandwidth, style)=>
    switch style
        "Triangular"    => triangular(source, bandwidth)
        "Gaussian"      => gaussian(source, bandwidth)
        "Epanechnikov"  => epanechnikov(source, bandwidth)
        "Logistic"      => logistic(source, bandwidth)
        "Log Logistic"  => loglogistic(source, bandwidth)
        "Cosine"        => cosine(source, bandwidth)
        "Sinc"          => sinc(source, bandwidth)
        "Laplace"       => laplace(source, bandwidth)
        "Quartic"       => quartic(source, bandwidth)
        "Parabolic"     => parabolic(source, bandwidth)
        "Exponential"   => exponential(source, bandwidth)
        "Silverman"     => silverman(source, bandwidth)
        "Cauchy"        => cauchy(source, bandwidth)
        "Tent"          => tent(source, bandwidth)
        "Wave"          => wave(source, bandwidth)
        "Power"         => power(source, bandwidth)
        "Morters"       => morters(source, bandwidth)

type coefficients
    float[] weights
    float sumw

precalculate(float bandwidth, string kernel)=>
    var coefficients[] c = array.new<coefficients>()
    if barstate.isfirst
        for i = 0 to 499
            coefficients w = coefficients.new(array.new<float>(), 0)
            float sumw = 0

            for j = 0 to 499
                diff = i - j
                weight = kernel(diff, bandwidth, kernel)
                sumw += weight
                w.weights.push(weight)

            w.sumw := sumw
            c.push(w)
        c
    else
        c

precalculate_nrp(bandwidth, kernel)=>
    var float[] weights = array.new<float>()
    var float sumw = 0
    if barstate.isfirst
        for i = 0 to bandwidth - 1
            j = math.pow(i, 2) / (math.pow(bandwidth, 2))
            weight = kernel(j, 1, kernel)
            weights.push(weight)
            sumw += weight
        [weights, sumw]
    else
        [weights, sumw]

multi_kernel_regression(source, bandwidth, deviations, style, labels, enable, line_style, text_color, bullish_color, bearish_color, size, repaint)=>
    var estimate_array = array.new<line>(500, line.new(na, na, na, na)) 
    var dev_upper_array = array.new<line>(500, line.new(na, na, na, na))
    var dev_lower_array = array.new<line>(500, line.new(na, na, na, na))
    var up_labels = array.new<label>(500, label.new(na, na))
    var down_labels = array.new<label>(500, label.new(na, na))      

    float current_price = na
    float previous_price = na
    float previous_price_delta = na
    float std_dev = na
    float upper_1 = na 
    float lower_1 = na
    float upper_2 = na 
    float lower_2 = na
    line estimate = na
    line dev_upper = na
    line dev_lower = na
    label bullish = na
    label bearish = na
    float nrp_sum = na
    float nrp_stdev = na
    color nrp_color = na

    if not repaint
        [weights, sumw] = precalculate_nrp(bandwidth, kernel)
        float sum   = 0.0
        float sumsq = 0.0
        for i = 0 to bandwidth - 1
            weight = weights.get(i)
            sum += nz(source[i]) * weight
        nrp_sum := sum / sumw
        direction = nrp_sum - nrp_sum[1] > 0
        nrp_color := direction ? bullish_color : bearish_color
        for i = 0 to bandwidth - 1
            sumsq += math.pow(source[i] - nrp_sum[i], 2)
        nrp_stdev := math.sqrt(sumsq / (bandwidth - 1)) * deviations
        if labels 
            if ta.crossover(nrp_sum, nrp_sum[1])
                label.new(bar_index, nrp_sum, "Up", xloc.bar_index, yloc.belowbar, bullish_color, label.style_label_up, text_color, size)
            if ta.crossunder(nrp_sum, nrp_sum[1])
                label.new(bar_index, nrp_sum, "Down", xloc.bar_index, yloc.abovebar, bearish_color, label.style_label_down, text_color, size)

        [nrp_sum, nrp_color, nrp_stdev]
    else
        coefficients[] c = precalculate(bandwidth, kernel)
        if barstate.isfirst
            for i = 499 to 0
                array.set(estimate_array, i, line.new(na, na, na, na))
                if enable
                    array.set(dev_upper_array, i, line.new(na, na, na, na))
                    array.set(dev_lower_array, i, line.new(na, na, na, na))
                if labels
                    array.set(up_labels, i, label.new(na, na))
                    array.set(down_labels,i,  label.new(na, na))    

        if barstate.islast
            for i = 0 to math.min(bar_index, 499)
                coefficient = c.get(i)
                float sum = 0
                float sumsq = 0

                for j = 0 to math.min(bar_index, 499)
                    diff = i - j
                    weight = coefficient.weights.get(j)
                    sum += source[j] * weight
                    sumsq += sq(source[j]) * weight

                current_price := sum / coefficient.sumw
                delta = current_price - previous_price

                if enable
                    std_dev := math.sqrt(math.max(sumsq / coefficient.sumw - sq(current_price), 0))
                    upper_2 := current_price + deviations * std_dev
                    lower_2 := current_price - deviations * std_dev

                estimate := array.get(estimate_array, i)

                if enable
                    dev_upper := array.get(dev_upper_array, i)
                    dev_lower := array.get(dev_lower_array, i)

                line.set_xy1(estimate, bar_index - i + 1, previous_price)
                line.set_xy2(estimate, bar_index - i, current_price)
                line.set_style(estimate, line_style)
                line.set_color(estimate, current_price > previous_price ? bearish_color : bullish_color)
                line.set_width(estimate, 3)

                if enable
                    line.set_xy1(dev_upper, bar_index - i + 1, upper_1)
                    line.set_xy2(dev_upper, bar_index - i , upper_2)
                    line.set_style(dev_upper, line_style)
                    line.set_color(dev_upper, current_price > previous_price ? bearish_color : bullish_color)
                    line.set_width(dev_upper, 3)
                    line.set_xy1(dev_lower, bar_index - i + 1, lower_1)
                    line.set_xy2(dev_lower, bar_index - i , lower_2)
                    line.set_style(dev_lower, line_style)
                    line.set_color(dev_lower, current_price > previous_price ? bearish_color : bullish_color)
                    line.set_width(dev_lower, 3)

                if labels
                    bullish := array.get(up_labels, i)
                    bearish := array.get(down_labels, i)

                    if delta > 0 and previous_price_delta < 0
                        label.set_xy(bullish, bar_index - i + 1, source[i])
                        label.set_text(bullish, 'Up')
                        label.set_color(bullish, bullish_color)
                        label.set_textcolor(bullish, text_color)
                        label.set_textalign(bullish, text.align_center)
                        label.set_size(bullish, size)
                        label.set_style(bullish, label.style_label_up)
                        label.set_yloc(bullish, yloc.belowbar)

                    if delta < 0 and previous_price_delta > 0
                        label.set_xy(bearish, bar_index - i + 1, source[i])
                        label.set_text(bearish, 'Down')
                        label.set_textcolor(bearish, text_color)
                        label.set_color(bearish, bearish_color)
                        label.set_textalign(bearish, text.align_center)
                        label.set_size(bearish, size)
                        label.set_style(bearish, label.style_label_down)
                        label.set_yloc(bearish, yloc.abovebar)

                previous_price := current_price
                upper_1 := upper_2
                lower_1 := lower_2
                previous_price_delta := delta

        if barstate.isconfirmed
            for i = array.size(up_labels) - 1 to 0
                label.set_xy(array.get(up_labels, i), na, na)
            for i = array.size(down_labels) - 1 to 0
                label.set_xy(array.get(down_labels, i), na, na)
    [nrp_sum, nrp_color, nrp_stdev]    

[nrp_sum, nrp_color, nrp_stdev] = multi_kernel_regression(source, bandwidth, deviations, kernel, labels, enable, line_style, text_color, bullish_color, bearish_color, size, repaint)

plot(nrp_sum, "Non Repaint MA", nrp_color)
plot(nrp_sum + nrp_stdev, "Non Repaint STDEV", nrp_color, display = enable ? display.all : display.none)
plot(nrp_sum - nrp_stdev, "Non Repaint STDEV", nrp_color, display = enable ? display.all : display.none)
