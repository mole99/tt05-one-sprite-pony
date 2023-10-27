default: openlane

RTL = src/top.sv \
      src/timing.sv \
      src/sprite_access.sv \
      src/sprite_data.sv \
      src/sprite_movement.sv \
      src/background.sv \
      src/synchronizer.sv \
      src/spi_receiver.sv

GL = src/gl/primitives.v \
     src/gl/sky130_fd_sc_hd.v \
     src/gl/tt_um_top_mole99.v

FPGA_ULX3S = fpga/rtl/ulx3s_top.sv \
	     fpga/rtl/pll40m.v \
	     src/tt_um_top_mole99.sv

# Simulation

sim-icarus:
	iverilog -g2012 -o top.vvp $(RTL) tb/tb_icarus.sv
	vvp top.vvp -fst

sim-icarus-gl:
	iverilog -g2012 -s tb -o top.vvp $(GL) tb/tb_icarus_gl.sv -DUSE_POWER_PINS=1
	vvp top.vvp -fst

sim-verilator:
	verilator --cc --exe --build -j 0 -Wall $(RTL) tb/tb_verilator.cpp -LDFLAGS "-lSDL2 -lpng16"
	./obj_dir/Vtop

sim-cocotb:
	python3 tb/tb_cocotb.py

# Various

sprites:
	python3 sprite2bit.py

animation.gif: images/
	convert -delay 1.666 -loop 0 images/*.png animation.gif

# FPGA

synth-ulx3s: ulx3s.json

build-ulx3s: ulx3s.bit

upload-ulx3s: ulx3s.bit
	openFPGALoader --board=ulx3s -f ulx3s.bit

ulx3s.json: $(RTL) $(FPGA_ULX3S)
	yosys -l $(basename $@)-yosys.log -DSYNTHESIS -DULX3S -DMODE_800x600 -p 'synth_ecp5 -top ulx3s_top -json $@' $(RTL) $(FPGA_ULX3S)

ulx3s.config: ulx3s.json fpga/constraints/ulx3s_v20.lpf
	nextpnr-ecp5 --85k --json $< \
		--lpf fpga/constraints/ulx3s_v20.lpf \
		--package CABGA381 \
		--textcfg $@

ulx3s.bit: ulx3s.config
	ecppack $< $@ --compress

clean:
	rm -f *.vvp *.vcd
	rm -f ulx3s.json ulx3s.config ulx3s.bit ulx3s-yosys.log

.PHONY: clean sim-icarus sim-verilator sim-cocotb sprites
