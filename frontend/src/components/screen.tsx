import React from 'react';
import {Spinner, Nav, Navbar, NavDropdown, Form, FormControl, Button, Card, Row, Col} from 'react-bootstrap';
import {Stage, Sprite, Container, Graphics} from '@inlet/react-pixi';

var lastValidationTime = 0;
var validationTimeout = null;


const Vertex = props => {
    const [dragging, setDragging] = React.useState(false);

    const mouseDown = e => {
        setDragging(true);
        let pos = [Math.round(Math.round(e.data.global.x/props.scale)*props.scale/2), Math.round(Math.round(e.data.global.y/props.scale)*props.scale/2)];
        props.update([Math.round(pos[0]*2/props.scale)-props.ox, Math.round(pos[1]*2/props.scale)-props.oy]);
    };

    const mouseMove = e => {
        if(dragging){
            let pos = [Math.round(Math.round(e.data.global.x/props.scale)*props.scale/2), Math.round(Math.round(e.data.global.y/props.scale)*props.scale/2)];
            props.update([Math.round(pos[0]*2/props.scale)-props.ox, Math.round(pos[1]*2/props.scale)-props.oy]);
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

    const position = [(Math.round(props.vertex[0]+props.ox)*props.scale/2), Math.round((props.vertex[1]+props.oy)*props.scale/2)];

    return <Graphics x={position[0]} y={position[1]} draw={draw} interactive={true} mousedown={mouseDown} mousemove={mouseMove} mouseup={mouseUp} />;
};


const Edge = props => {
    const adjustX = x => Math.round((x+props.ox)*props.scale);
    const adjustY = y => Math.round((y+props.oy)*props.scale);
    const start = [adjustX(props.start[0]), adjustY(props.start[1])];
    const end = [adjustX(props.end[0]), adjustY(props.end[1])];
    const dist = (x, y) => (x[0]-y[0])*(x[0]-y[0])+(x[1]-y[1])*(x[1]-y[1]);
    const u0 = props.os;
    const u1 = props.oe;
    const v0 = props.start;
    const v1 = props.end;
    const du = dist(u0, u1);
    const dv = dist(v0, v1);
    const r = dv/du;

    const draw = React.useCallback(g => {
        g.clear();
        if(r-1>props.epsilon/1000000){
            g.beginFill(0xffff00);
            g.lineStyle(1, 0xffff00, 1);
        }
        else if(1-r>props.epsilon/1000000){
            g.beginFill(0x0000ff);
            g.lineStyle(1, 0x0000ff, 1);
        }
        else{
            g.beginFill(0xff0000);
            g.lineStyle(1, 0xff0000, 1);
        }
        g.moveTo(start[0], start[1]);
        g.lineTo(end[0], end[1]);
        g.endFill();
    });

    return <Graphics draw={draw} />;
};

const Problem = (props) => {
    let vertices = [];
    let setVertices = [];
    const [epsilon, setEpsilon] = React.useState(0);
    const [v2e, setV2e] = React.useState([]);
    const [dislikes, setDislikes] = React.useState(0);
    const [valid, setValid] = React.useState(false);
    const [loading, setLoading] = React.useState(false);
    const [scale, setScale] = React.useState(4);

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

    const calculateDislikes = vs => {
        let dislikes = 0;
        for(var h of props.problem.hole){
            let m = 100000000;
            for(var i=0; i<props.problem.figure.vertices.length; ++i){
                const v = vs[i];
                const d = (h[0]-v[0])*(h[0]-v[0]) + (h[1]-v[1])*(h[1]-v[1]);
                m = Math.min(m, d);
            }
            dislikes += m;
        }
        return dislikes;
    };

    React.useEffect(() => {
        let vertex_to_edges = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            setVertices[i](props.problem.figure.vertices[i]);
            vertex_to_edges.push([]);
        }
        for(var edge of props.problem.figure.edges){
            vertex_to_edges[edge[0]].push(edge[1]);
            vertex_to_edges[edge[1]].push(edge[0]);
        }
        setEpsilon(props.problem.epsilon);
        setV2e(vertex_to_edges);
        setDislikes(calculateDislikes(props.problem.figure.vertices));
        updateValidity();
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
    }, [props, scale]);

    const updateValidity = (vs=vertices) => {
        const now = Date.now();
        if(now-lastValidationTime>500){
            lastValidationTime = now;
            fetch("validate", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    problem: props.problem,
                    vertices: vs,
                })
            }).then(res => res.json().then(dat => {
                setValid(dat.valid);
            }));
        }
        else{
            if(validationTimeout!=null){
                clearTimeout(validationTimeout);
            }
            validationTimeout = setTimeout(updateValidity, 500);
        }
    };

    const updateVertex = n => v => {
        setVertices[n](v);
        setDislikes(calculateDislikes(vertices));
        updateValidity();
    }

    const up = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = vertices[i];
            const nv = [v[0], v[1]-1];
            setVertices[i](nv);
            nvs.push(nv);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    };

    const down = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = vertices[i];
            const nv = [v[0], v[1]+1];
            setVertices[i](nv);
            nvs.push(nv);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    };

    const left = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = vertices[i];
            const nv = [v[0]-1, v[1]];
            setVertices[i](nv);
            nvs.push(nv);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    };

    const right = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = vertices[i];
            const nv = [v[0]+1, v[1]];
            setVertices[i](nv);
            nvs.push(nv);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    };

    const hflip = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = vertices[i];
            const nv = [max-v[0], v[1]];
            setVertices[i](nv);
            nvs.push(nv);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    };

    const vflip = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = vertices[i];
            const nv = [v[0], max-v[1]];
            setVertices[i](nv);
            nvs.push(nv);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    };

    const search = () => {
        setLoading(true);
        fetch("search", {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                problem: props.problem,
                vertices: vertices.slice(0, props.problem.figure.vertices.length),
            })
        }).then(res => res.json().then(dat => {
            let nvs = [];
            for(var i=0; i<props.problem.figure.vertices.length; ++i){
                const v = dat[i];
                setVertices[i](v);
                nvs.push(v);
            }
            setDislikes(calculateDislikes(nvs));
            updateValidity(nvs);
            setLoading(false);
        }));
    };

    const reset = () => {
        let nvs = [];
        for(var i=0; i<props.problem.figure.vertices.length; ++i){
            const v = props.problem.figure.vertices[i];
            setVertices[i](v);
            nvs.push(v);
        }
        setDislikes(calculateDislikes(nvs));
        updateValidity(nvs);
    }

    const zoomin = () => {
        setScale(scale+2);
    };

    const zoomout = () => {
        setScale(Math.max(2, scale-2));
    };

    const download = () => {
        const dat = {vertices: vertices};
        const blob = new Blob([JSON.stringify(dat, null, 2)], {type : 'application/json'});
        if(window.navigator && window.navigator.msSaveBlob){
            console.log("a");
            window.navigator.msSaveBlob(blob, `answer_${props.number}.json`);
        }
        else{
            let reader = new FileReader();
            reader.onload = e => {
                let link = document.getElementById("download_link");
                link.href = e.target.result;
                link.download = `answer_${props.number}.json`;
                link.click();
            };
            reader.readAsDataURL(blob);
        }
    };

    const loader = (
        <div style={{display: "table", width: "100%", height: "100%", top: 0, left: 0, position: "fixed", backgroundColor: '#fff', opacity: 0.6, zIndex:100}}>
            <div style={{display: "table-cell", textAlign: "center", verticalAlign: "middle"}}>
                <Spinner animation="border" role="status" variant="info" style={{width: "5rem", height: "5rem"}}>
                    <span className="sr-only">Loading...</span>
                </Spinner>
            </div>
        </div>
    );

    return (
        <div className="mx-3">
            <Row>
                <Col sm={3} className="m-0 p-1">
                    <Card className="m-1 px-1 py-0" style={{borderWidth: 3, borderColor: "rgba(0, 0, 0, 0.8)"}}>
                    <Card.Body className="text-center py-1">
                        <Card.Title className="mb-0">Problem</Card.Title>
                        <div style={{fontSize: "2.2em", fontWeight: "bold", userSelect: "none"}}>#{props.number}</div>
                    </Card.Body>
                    </Card>
                </Col>
                <Col sm={3} className="m-0 p-1">
                    <Card className="m-1 px-1 py-0" style={{borderWidth: 3, borderColor: "rgba(0, 0, 0, 0.8)"}}>
                    <Card.Body className="text-center py-1">
                        <Card.Title className="mb-0">Dislikes</Card.Title>
                        <div style={{fontSize: "2.2em", fontWeight: "bold", userSelect: "none"}}>{dislikes}</div>
                    </Card.Body>
                    </Card>
                </Col>
                <Col sm={3} className="m-0 p-1">
                    <Card className="m-1 px-1 py-0" style={{borderWidth: 3, borderColor: "rgba(0, 0, 0, 0.8)"}}>
                    <Card.Body className="text-center py-1">
                        <Card.Title className="mb-0">Epsilon</Card.Title>
                        <div style={{fontSize: "2.2em", fontWeight: "bold", userSelect: "none"}}>{props.problem.epsilon}</div>
                    </Card.Body>
                    </Card>
                </Col>
                <Col sm={3} className="m-0 p-1">
                    <Card className="m-1 px-1 py-0" style={{borderWidth: 3, borderColor: "rgba(0, 0, 0, 0.8)"}}>
                    <Card.Body className="text-center py-1">
                        <Card.Title className="mb-0">Status</Card.Title>
                        {valid?
                            <div style={{fontSize: "2.2em", color: "green", fontWeight: "bold", userSelect: "none"}}>Valid</div> :
                            <div style={{fontSize: "2.2em", color: "red", fontWeight: "bold", userSelect: "none"}}>Invalid</div>
                        }
                    </Card.Body>
                    </Card>
                </Col>
            </Row>
            <Row>
                <Col sm={1}>
                    <Row className="my-1">
                        <Button onClick={up} className="ml-1" style={{width: "6em"}}>Up</Button>
                    </Row>
                    <Row className="my-1">
                        <Button onClick={down} className="ml-1" style={{width: "6em"}}>Down</Button>
                    </Row>
                    <Row className="my-1">
                        <Button onClick={left} className="ml-1" style={{width: "6em"}}>Left</Button>
                    </Row>
                    <Row className="my-1">
                        <Button onClick={right} className="ml-1" style={{width: "6em"}}>Right</Button>
                    </Row>
                    <Row className="my-1">
                        <Button onClick={hflip} className="ml-1" style={{width: "6em"}}>HFlip</Button>
                    </Row>
                    <Row className="my-1">
                        <Button onClick={vflip} className="ml-1" style={{width: "6em"}}>VFlip</Button>
                    </Row>
                    <Row className="my-1 mt-3">
                        <Button variant="info" onClick={search} className="ml-1" style={{width: "6em"}}>Search</Button>
                    </Row>
                    <Row className="my-1">
                        <Button variant="info" onClick={zoomin} className="ml-1" style={{width: "6em"}}>+</Button>
                    </Row>
                    <Row className="my-1">
                        <Button variant="info" onClick={zoomout} className="ml-1" style={{width: "6em"}}>-</Button>
                    </Row>
                    <Row className="my-1 mt-3">
                        <Button variant="success" onClick={download} className="ml-1" style={{width: "6em"}}>Download</Button>
                    </Row>
                    <Row className="my-1">
                        <Button variant="danger" onClick={reset} className="ml-1" style={{width: "6em"}}>Reset</Button>
                    </Row>
                </Col>
                <Col sm={11}>
                    <Stage width={max*scale+margin*scale*2} height={max*scale+margin*scale*2} options={{backgroundColor: 0x808080}}>
                        <Graphics draw={draw} />
                        {props.problem.figure.edges.map((e, n) => <Edge key={`edge${n}`} scale={scale} epsilon={props.problem.epsilon} os={props.problem.figure.vertices[e[0]]} oe={props.problem.figure.vertices[e[1]]} start={vertices[e[0]]} end={vertices[e[1]]} ox={ox} oy={oy} />)}
                        {props.problem.figure.vertices.map((v, n) => <Vertex key={`vertex${n}`} scale={scale} vertex={vertices[n]} ox={ox} oy={oy} update={updateVertex(n)} />)}
                    </Stage>
                </Col>
            </Row>
            <a id="download_link" hidden></a>
            {loading? loader : <></>}
        </div>
    );
};


const Screen = () => {
    const [problems, setProblems] = React.useState([]);
    const [currentProblem, setCurrentProblem] = React.useState(null);
    const [currentProblemNumber, setCurrentProblemNumber] = React.useState(1);

    React.useEffect(() => {
        fetch("problems").then(res => {
            res.json().then(dat => {
                setProblems(dat);
                setCurrentProblem(dat[0]);
            });
        });
    }, []);

    const loader = (
        <div style={{display: "table", width: "100%", height: "100%", top: 0, left: 0, position: "fixed", backgroundColor: '#fff', opacity: 0.6, zIndex:100}}>
            <div style={{display: "table-cell", textAlign: "center", verticalAlign: "middle"}}>
                <Spinner animation="border" role="status" variant="info" style={{width: "5rem", height: "5rem"}}>
                    <span className="sr-only">Loading...</span>
                </Spinner>
            </div>
        </div>
    );

    if(problems.length==0 || currentProblem==null) return loader;

    const update = n => () => {
        setCurrentProblem(problems[n]);
        setCurrentProblemNumber(n+1);
    };

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
        <Problem problem={currentProblem} number={currentProblemNumber} />
    </>);
};

export default Screen;
