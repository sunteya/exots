# frozen_string_literal: true

module Exots
  class Runner
    attr_reader :bin, :args

    def initialize(bin, args: [])
      @bin = bin
      @args = args
    end

    def command(script, socket_path, pid_path = nil)
      cmd_args = [@bin] + @args + [script, '--socket', socket_path]
      cmd_args += ['--pid', pid_path] if pid_path
      cmd_args
    end

    Node = new('node')
    Bun = new('bun')
    Python = new('python3')
  end
end
