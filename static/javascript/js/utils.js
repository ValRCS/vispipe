function onDragStart(event)
{
    // store a reference to the data
    // the reason for this is because of multitouch
    // we want to track the movement of this particular touch
    var i;
    var obj;

    this.target = event.target;
    this.ischild = false;
    for (i=0; i<event.target.children.length; i++){
        this.child = event.target.children[i];
        if (this.child.type !== undefined && this.child.containsPoint(event.data.global)) {
            obj = new PIXI.Graphics();
            this.ischild = obj;
            app.stage.addChildAt(this.ischild, app.stage.children.length);
            break;
        }
    }

    this.start_pos = new PIXI.Point(event.data.global.x, event.data.global.y);
    this.data = event.data;
    this.dragging = this.data.getLocalPosition(this.parent);

    if (!this.ischild){
        this.alpha = 0.5;
        app.stage.setChildIndex(this, app.stage.children.length-1);
    } else {
        app.stage.setChildIndex(this, app.stage.children.length-2);
    }
}

function onDragEnd(event)
{
    // Close drag logic
    this.alpha = 1;
    this.dragging = false;
    // set the interaction data to null
    this.data = null;

    if (this.ischild){
        var target_conn = point_to_conn(event.data.global); // The connection we arrived to
        if (target_conn && target_conn.type !== this.child.type){
            var input = (this.child.type === 'input') ? this.child : target_conn;
            var output = (this.child.type === 'output') ? this.child : target_conn;
            var input_node = input.parent.node;
            var output_node = output.parent.node;
            // If we connect a input node which is already connected we need to remap
            // its connection to the new output
            // If we connect a output node which is already connected we need to APPEND
            // its new connection
            if (input.connection){
                input.connection.connection.splice(input.connection.connection.indexOf(input), 1);
                input.connection.conn_line.splice(input.connection.conn_line.indexOf(input.conn_line), 1);
                input.conn_line.destroy();
                input.conn_line = [];
                input.connection = null;
            }
            input.connection = output;
            output.connection.push(input);
            this.ischild.from = input;
            this.ischild.to = output;
            input.conn_line = this.ischild;
            output.conn_line.push(this.ischild);
            pipeline.add_connection(output_node.block, output_node.id, output.index,
                                    input_node.block, input_node.id, input.index);
        } else {
            this.ischild.destroy();
        }
    }

    this.ischild = false;
    this.child = null;
    this.target = null;
}

function point_to_conn(point){
    var i, child;
    var root_obj = app.renderer.plugins.interaction.hitTest(point);

    if (root_obj){
        for (i=0; i<root_obj.children.length; i++){
            child = root_obj.children[i];
            if (child.type !== undefined && child.containsPoint(point)) {
                return child;
            }
        }
    }
    return null;
}

function onDragMove(event)
{
    if (this.dragging && !this.ischild)
    {
        var newPosition = this.data.getLocalPosition(this.parent);
        this.position.x += (newPosition.x - this.dragging.x);
        this.position.y += (newPosition.y - this.dragging.y);
        this.dragging = newPosition;
        update_all_lines(this.target.node);
    } else if (this.ischild) {
        update_line(this.ischild, this.start_pos, event.data.global);
    }
}

function onMouseOver(event){
    if (!this.dragging){
        event.target.alpha = 0.9;
    }
}

function onMouseOut(event){
    if (!this.dragging){
        event.currentTarget.alpha = 1;
    }
}

function update_all_lines(node){
    var i, j, from, to, from_pos, to_pos;

    for (i=0; i<node.in_c.length; i++){
        if (node.in_c[i].conn_line){
            from = node.in_c[i].conn_line.from;
            from_pos = new PIXI.Point(from.worldTransform.tx, from.worldTransform.ty);
            to = node.in_c[i].conn_line.to;
            to_pos = new PIXI.Point(to.worldTransform.tx, to.worldTransform.ty);
            update_line(node.in_c[i].conn_line, to_pos, from_pos) // Is inverted
            app.stage.setChildIndex(node.in_c[i].conn_line, app.stage.children.length-1);
        }
    }

    for (i=0; i<node.out_c.length; i++){
        for (j=0; j<node.out_c[i].conn_line.length; j++){
            if (node.out_c[i].conn_line[j]){ 
                from = node.out_c[i].conn_line[j].from;
                from_pos = new PIXI.Point(from.worldTransform.tx, from.worldTransform.ty);
                to = node.out_c[i].conn_line[j].to;
                to_pos = new PIXI.Point(to.worldTransform.tx, to.worldTransform.ty);
                update_line(node.out_c[i].conn_line[j], to_pos, from_pos) // Is inverted
                app.stage.setChildIndex(node.out_c[i].conn_line[j], app.stage.children.length-1);
            }
        }
    }
}

function update_line(line, from, to){
    line.clear();
    line.moveTo(from.x, from.y);
    line.lineStyle(3, 0x46b882, 1);

    var xctrl = (1.5 * to.x + 0.5 * from.x) / 2;
    var delta = to.y - from.y;
    var yctrl;
    if (delta < 0){
        yctrl = (to.y + from.y) / 2 + Math.min(Math.abs(delta), 50);
    } else {
        yctrl = (to.y + from.y) / 2 - Math.min(Math.abs(delta), 50);
    }

    line.quadraticCurveTo(xctrl, yctrl, to.x, to.y);
}

function name_to_size(name){
    var w = Math.max(60, 25 + name.length * 8);
    var h = 40; //name.length * 20;
    return [w, h];
}

function draw_rect(width, height, color, scale){
    var obj = new PIXI.Graphics();
    obj.lineStyle(2, 0x000000, 1);
    obj.beginFill(color);
    obj.drawRect(0, 0, width * scale, height * scale);
    obj.endFill();
    return obj;
}

function draw_block(name){
    var [width, height] = name_to_size(name);
    var obj = draw_rect(width, height, BLOCK_COLOR, 1);
    var text = draw_text(name);
    text.anchor.set(0.5, 0.5);
    text.position.set(obj.width / 2, obj.height / 2);
    obj.addChild(text);
    return [obj, text];
}

function draw_text(text, scale=1){
    text = new PIXI.Text(text,
        {
            fontFamily: FONT,
            fontSize: FONT_SIZE * scale,
            fill: TEXT_COLOR,
            align: 'right'
        });
    return text;
}

function draw_conn(inputs, outputs, rect){
    var width = rect.width;
    var height = rect.height;

    var in_even = ((inputs % 2 === 0) ? 1 : 0);
    var out_even = ((outputs % 2 === 0) ? 1 : 0);
    var in_step = width / inputs / (in_even + 1);
    var out_step = width / outputs / (out_even + 1);

    var radius = Math.max(6, 10 - (2 * inputs));

    var input_conn = [];
    var output_conn = [];

    function draw_circle(){
        var obj = new PIXI.Graphics();
        obj.lineStyle(2, 0x000000, 1);
        obj.beginFill(INPUT_COLOR);
        obj.drawCircle(0, 0, radius);
        obj.endFill();
        return obj;
    }

    var x = rect.position.x + width / 2 - 1;
    var y = height - 45;
    var offset = 0;
    for (var i = 0; i < inputs; i++){
        var obj = draw_circle()
        if (i !== 0 || inputs % 2 === 0) {
            offset = (-1)**i * (1 + Math.floor((i - 1 + in_even) / 2)) * in_step;
        }
        obj.position.set(x + offset, y);
        input_conn.push(obj);
    }

    y = height + 1;
    offset = 0;
    for (i = 0; i < outputs; i++){
        obj = draw_circle()
        if (i !== 0 || outputs % 2 === 0) {
            offset = (-1)**i * (1 + Math.floor((i - 1 + out_even) / 2)) * out_step;
        }
        obj.position.set(x + offset, y);
        output_conn.push(obj);
    }

    function sort_logic(x, y){
        if (x.position.x < y.position.x){
            return -1;
        } else if (x.position.x > y.position.x){
            return 1;
        }
        return 0;
    }

    input_conn.sort(sort_logic);
    output_conn.sort(sort_logic);
    return [input_conn, output_conn];
}