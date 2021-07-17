import React from 'react';
import {Spinner, Nav, Navbar, NavDropdown, Form, FormControl, Button} from 'react-bootstrap';
import {Stage, Sprite, Container, Graphics} from '@inlet/react-pixi';

const scale = 4;


const Vertex = props => {
    const [dragging, setDragging] = React.useState(false);

    const mouseDown = e => {
        setDragging(true);
        let pos = [Math.floor(Math.floor(e.data.global.x/scale)*scale/2), Math.floor(Math.floor(e.data.global.y/scale)*scale/2)];
        props.update([Math.floor(pos[0]*2/scale)-props.ox, Math.floor(pos[1]*2/scale)-props.oy]);
    };

    const mouseMove = e => {
        if(dragging){
            setDragging(true);
            let pos = [Math.floor(Math.floor(e.data.global.x/scale)*scale/2), Math.floor(Math.floor(e.data.global.y/scale)*scale/2)];
            props.update([Math.floor(pos[0]*2/scale)-props.ox, Math.floor(pos[1]*2/scale)-props.oy]);
        }
    };

    const mouseUp = () => { setDragging(false); };

    const draw = React.useCallback(g => {
        g.clear();
        g.beginFill(0xff0000, dragging? 0.5:1);
        g.lineStyle(1, 0xff0000, dragging? 0.5:1);
        g.drawCircle(position[0], position[1], 4);
        g.endFill();
    });

    const position = [(Math.floor(props.vertex[0]+props.ox)*scale/2), Math.floor((props.vertex[1]+props.oy)*scale/2)];

    return <Graphics x={position[0]} y={position[1]} draw={draw} interactive={true} mousedown={mouseDown} mousemove={mouseMove} mouseup={mouseUp} />;
};


const Edge = props => {
    const adjustX = x => Math.floor((x+props.ox)*scale);
    const adjustY = y => Math.floor((y+props.oy)*scale);
    const start = [adjustX(props.start[0]), adjustY(props.start[1])];
    const end = [adjustX(props.end[0]), adjustY(props.end[1])];

    const draw = React.useCallback(g => {
        g.clear();
        g.beginFill(0xff0000);
        g.lineStyle(1, 0xff0000, 1);
        g.moveTo(start[0], start[1]);
        g.lineTo(end[0], end[1]);
        g.endFill();
    });

    return <Graphics draw={draw} />;
};


const Problem = (props) => {
    let vertices = [];
    let setVertices = [];

    for(var i=0; i<100; ++i){
        const [vertex, setVertex] = React.useState(i<props.problem.figure.vertices.length? props.problem.figure.vertices[i] : [0, 0]);
        vertices.push(vertex);
        setVertices.push(setVertex);
    }

    const margin = 20;
    const xmax = Math.max(...props.problem.hole.map(v => v[0]));
    const ymax = Math.max(...props.problem.hole.map(v => v[1]));
    const xmin = Math.min(...props.problem.hole.map(v => v[0]));
    const ymin = Math.min(...props.problem.hole.map(v => v[1]));
    const max = Math.max(xmax, ymax);
    const ox = margin + Math.floor((max-xmax)/2);
    const oy = margin + Math.floor((max-ymax)/2);

    React.useEffect(() => {
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            setVertices[i](props.problem.figure.vertices[i]);
        }
    }, [props]);

    const draw = React.useCallback(g => {
        g.clear();
        g.beginFill(0xffffff);
        g.lineStyle(1, 0xffffff, 1);
        g.drawPolygon(props.problem.hole.map(x => [(x[0]+ox)*scale, (x[1]+oy)*scale]).flatMap(x => x));
        g.endFill();
        for(var bonus of props.problem.bonuses){
            let v = bonus.position;
            let drawBonus = (fillstyle, linestyle, pos) => {
                g.beginFill(...fillstyle);
                g.lineStyle(...linestyle);
                g.drawCircle((pos[0]+ox)*scale, (pos[1]+oy)*scale, 10);
                g.endFill();
            };
            if(bonus.bonus=="GLOBALIST"){ drawBonus([0xffff00, 0.5], [1, 0xffff00, 0.5], v); }
            else if(bonus.bonus=="WALLHACK"){ drawBonus([0xff8000, 0.5], [1, 0xff8000, 0.5], v); }
            else{ drawBonus([0x0000ff, 0.5], [1, 0x0000ff, 0.5], v); }
        }
        for(var x of [...Array(max*scale+margin*scale*2).keys()]){
            g.beginFill(0x000000, 0.2);
            g.lineStyle(1, 0x000000, 0.2);
            g.moveTo(x*scale, 0);
            g.lineTo(x*scale, max*scale+margin*scale*2);
            g.moveTo(0, x*scale);
            g.lineTo(max*scale+margin*scale*2, x*scale);
            g.endFill();
        }
    }, [props]);

    const updateVertex = n => v => { setVertices[n](v); }

    return (
        <Stage width={max*scale+margin*scale*2} height={max*scale+margin*scale*2} options={{backgroundColor: 0x808080}}>
            <Graphics draw={draw} />
            {props.problem.figure.edges.map((e, n) => <Edge key={`edge${n}`} start={vertices[e[0]]} end={vertices[e[1]]} ox={ox} oy={oy} />)}
            {props.problem.figure.vertices.map((v, n) => <Vertex key={`vertex${n}`} vertex={vertices[n]} ox={ox} oy={oy} update={updateVertex(n)} />)}
        </Stage>
    );
};


const Screen = () => {
    const [problems, setProblems] = React.useState([]);
    const [currentProblem, setCurrentProblem] = React.useState(null);

    React.useEffect(() => {
        fetch("problems").then(res => {
            res.json().then(dat => {
                setProblems(dat);
                setCurrentProblem(dat[0]);
            });
        });
    }, []);

    if(problems.length==0 || currentProblem==null) return (
        <div style={{display: "table", width: "100%", height: "100%", top: 0, left: 0, position: "fixed"}}>
            <div style={{display: "table-cell", textAlign: "center", verticalAlign: "middle"}}>
                <Spinner animation="border" role="status" variant="info" style={{width: "5rem", height: "5rem"}}>
                    <span className="sr-only">Loading...</span>
                </Spinner>
            </div>
        </div>
    );

    const update = n => () => { setCurrentProblem(problems[n]); };

    return (<>
        <Navbar bg="dark" variant="dark" expand="lg">
            <Navbar.Brand href="#home">ICFPC2021</Navbar.Brand>
            <Navbar.Toggle aria-controls="basic-navbar-nav" />
            <Navbar.Collapse id="basic-navbar-nav">
                <Nav className="mr-auto">
                    <NavDropdown title="Problems">
                        {problems.map((problem, n) => <NavDropdown.Item key={`problem${n+1}`} onClick={update(n)}>{`Problem #${n+1}`}</NavDropdown.Item>)}
                    </NavDropdown>
                </Nav>
            </Navbar.Collapse>
        </Navbar>
        <div style={{margin: "2em"}}>
            <Problem problem={currentProblem} />
        </div>
    </>);
};

export default Screen;
