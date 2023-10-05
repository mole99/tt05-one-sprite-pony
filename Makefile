default: openlane

RTL = src/top.sv \
      src/timing.sv \
      src/sprite_access.sv \
      src/sprite_data.sv \
      src/sprite_movement.sv \
      src/background.sv \
      src/synchronizer.sv \
      src/spi_receiver.sv

FPGA_ULX3S = fpga/rtl/ulx3s_top.sv \
	     fpga/rtl/GFX_hdmi.v \
	     fpga/rtl/GFX_PLL.v \
	     fpga/rtl/TMDS_encoder.v

FPGA_ICEBREAKER = fpga/rtl/icebreaker_top.sv

sim-icarus:
	iverilog -g2012 -o top.vvp $(RTL) tb/tb_icarus.sv
	vvp top.vvp -fst

sim-verilator:
	verilator --cc --exe --build -j 0 -Wall $(RTL) tb/tb_verilator.cpp -LDFLAGS "-lSDL2 -lpng16"
	./obj_dir/Vtop

sim-cocotb:
	python3 tb/tb_cocotb.py

openlane: $(RTL)
	python3 -m openlane --dockerized --flow Classic --pdk sky130A config.json

sprites:
	python3 sprite2bit.py

animation.gif: images/
	convert -delay 1.666 -loop 0 images/*.png animation.gif

synth-icebreaker: icebreaker.json

build-icebreaker: icebreaker.bit

upload-icebreaker: icebreaker.bit
	openFPGALoader --board=ice40_generic -f icebreaker.bit

icebreaker.json: $(RTL) $(FPGA_ICEBREAKER)
	yosys -l $(basename $@)-yosys.log -DSYNTHESIS -DICEBREAKER -p 'synth_ice40 -top icebreaker_top -json $@' $(RTL) $(FPGA_ICEBREAKER)

icebreaker.asc: icebreaker.json fpga/constraints/icebreaker.pcf
	nextpnr-ice40 --up5k --json $< \
		--pcf fpga/constraints/icebreaker.pcf \
		--package sg48 \
		--asc $@

icebreaker.bit: icebreaker.asc
	icepack $< $@

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
	ecppack $< $@

clean:
	rm -f *.vvp *.vcd
	rm -rf openlane_run runs
	rm -f icebreaker.json icebreaker.asc icebreaker.bit icebreaker-yosys.log
	rm -f ulx3s.json ulx3s.config ulx3s.bit ulx3s-yosys.log

.PHONY: clean openlane sim-icarus sim-verilator sprites
